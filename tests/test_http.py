import json
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
from pathlib import Path

from cenacle.server import make_server
from cenacle.core import Project
from cenacle.folder_picker import PickerError

ROOT = Path(__file__).resolve().parents[1]


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.server = make_server(0, self.root / "runtime")
        self.url = "http://127.0.0.1:" + str(self.server.server_address[1])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        (self.root / "code").mkdir()
        self.p = Project.create(self.root / "project", "HTTP test", "Verify transport", self.root / "code")
        self.server.app.add(self.p)

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.server.app.close()
        self.temp.cleanup()

    def request(self, route, data=None, headers=None, owner=True):
        hdrs = {"Authorization": "Bearer " + self.server.app.secret} if owner else {}
        hdrs.update(headers or {})
        if data is not None:
            hdrs["Content-Type"] = "application/json"
        req = urllib.request.Request(self.url+route, data=json.dumps(data).encode() if data is not None else None, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=3) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as r:
            with r:
                return r.code, r.headers, r.read()

    def cmd(self, action, args, credential=None):
        status, _, body = self.request("/api/command", {"project": self.p.id, "action": action, "args": args},
                                      {"Authorization": "Bearer "+credential} if credential else None)
        self.assertEqual(200, status, body)
        return json.loads(body)

    def test_ui_assets_cookie_and_origin_restrictions(self):
        status, headers, body = self.request("/", owner=False)
        self.assertEqual(200, status)
        self.assertIn(b'app.js', body)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        status, _, _ = self.request("/api/state?project="+self.p.id, owner=False)
        self.assertEqual(401, status)
        status, _, _ = self.request("/api/state?project="+self.p.id, headers={"Origin": "https://untrusted.example"})
        self.assertEqual(403, status)
        status, _, _ = self.request("/", headers={"Host": "rebind.example"})
        self.assertEqual(403, status)
        status, _, body = self.request("/app.js", owner=False)
        self.assertEqual(200, status)
        self.assertIn(b"general_context", body)

    def test_native_folder_selection_and_cancel_without_creating_project(self):
        before = set(self.server.app.projects)
        with patch("cenacle.server.choose_folder", return_value=str(self.root / "code")) as picker:
            status, _, body = self.request("/api/pick-folder", {"path": str(self.root), "title": "Workspace"})
            self.assertEqual(200, status)
            self.assertEqual(str(self.root / "code"), json.loads(body)["path"])
            picker.assert_called_once_with(str(self.root), "Workspace", allow_new=False)
        with patch("cenacle.server.choose_folder", return_value=None):
            status, _, body = self.request("/api/pick-folder", {})
            self.assertEqual(200, status)
            self.assertEqual({"path": None, "cancelled": True}, json.loads(body))
        self.assertEqual(before, set(self.server.app.projects))

    def test_native_folder_dialog_requires_owner_and_same_origin(self):
        with patch("cenacle.server.choose_folder") as picker:
            status, _, _ = self.request("/api/pick-folder", {}, owner=False)
            self.assertEqual(401, status)
            status, _, _ = self.request("/api/pick-folder", {}, headers={"Origin": "https://untrusted.example"})
            self.assertEqual(403, status)
            picker.assert_not_called()

    def test_native_folder_busy_and_failure_release_dialog_lock(self):
        self.server.app.picker_lock.acquire()
        try:
            with patch("cenacle.server.choose_folder") as picker:
                status, _, _ = self.request("/api/pick-folder", {})
                self.assertEqual(409, status)
                picker.assert_not_called()
        finally:
            self.server.app.picker_lock.release()
        with patch("cenacle.server.choose_folder", side_effect=PickerError("No desktop")):
            status, _, body = self.request("/api/pick-folder", {})
            self.assertEqual(503, status)
            self.assertIn("No desktop", json.loads(body)["error"])
        self.assertFalse(self.server.app.picker_lock.locked())

    def test_expired_browser_session_renews_and_creates_nested_folder(self):
        # Simulate a browser left open across a coordinator restart.
        port = self.server.server_address[1]
        stale = {"Cookie": f"cenacle_{port}=old-server-token"}
        workspace = self.root / "Code with spaces Clé"
        workspace.mkdir()
        source = workspace / "main.py"
        source.write_text("# Existing code stays intact\n", encoding="utf-8")
        data = {"workspace": str(workspace), "name": "New room", "goal": "Build safely", "general_context": "Shared context"}
        status, _, body = self.request("/api/create", data, stale, owner=False)
        self.assertEqual(401, status)
        self.assertEqual("owner_session_required", json.loads(body)["code"])
        self.assertFalse((workspace / ".cenacle").exists())
        status, headers, _ = self.request("/api/session", headers={"X-Cenacle-UI": "1", **stale}, owner=False)
        self.assertEqual(200, status)
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        status, _, body = self.request("/api/create", data, {"Cookie": cookie}, owner=False)
        self.assertEqual(200, status, body)
        config = json.loads((workspace / ".cenacle" / "cenacle.json").read_text("utf-8"))
        self.assertEqual(str(workspace), config["project"]["workspace"])
        self.assertTrue((workspace / ".cenacle" / "cenacle_files").is_dir())
        self.assertEqual("# Existing code stays intact\n", source.read_text("utf-8"))

    def test_session_renewal_cannot_be_triggered_cross_origin(self):
        status, _, _ = self.request("/api/session", owner=False)
        self.assertEqual(403, status)
        status, _, _ = self.request("/api/session", headers={"X-Cenacle-UI": "1", "Origin": "https://untrusted.example"}, owner=False)
        self.assertEqual(403, status)

    def test_new_coordination_folder_picker_allows_missing_path(self):
        selected = self.root / "code" / ".cenacle"
        with patch("cenacle.server.choose_folder", return_value=str(selected)) as picker:
            status, _, body = self.request("/api/pick-folder", {"path": str(self.root / "code"), "allow_new": True})
            self.assertEqual(200, status)
            self.assertEqual(str(selected), json.loads(body)["path"])
            self.assertTrue(picker.call_args.kwargs["allow_new"])
        self.assertFalse(selected.exists())

    def test_watch_does_not_wake_on_read_receipts_but_does_on_pause(self):
        a = self.cmd("register", {"handle": "test"})
        self.cmd("control", {"paused": False})
        seq = len(self.p.events)
        self.request("/api/inbox", {"project": self.p.id, "bootstrap": True}, {"Authorization": "Bearer "+a["credential"]})
        def watch():
            status, _, data = self.request("/api/watch", {"project": self.p.id, "after": seq, "timeout": .05}, {"Authorization": "Bearer "+a["credential"]})
            self.assertEqual(200, status)
            return json.loads(data)
        self.assertFalse(watch()["changed"])
        self.cmd("control", {"paused": True})
        self.assertTrue(watch()["changed"])
        self.assertTrue(watch()["control"]["paused"])

    def test_full_message_search_and_notes_separate(self):
        a = self.cmd("register", {"handle": "test"})
        self.cmd("control", {"paused": False})
        self.cmd("note", {"body": "Private working note visible to owner"}, a["credential"])
        m = self.cmd("send", {"room": "agent_scratch", "body": "needle " + "X"*20000}, a["credential"])
        _, _, body = self.request("/api/history?project="+self.p.id+"&room=agent_scratch&q=needle")
        self.assertEqual(1, len(json.loads(body)["messages"]))
        _, _, body = self.request("/api/history?project="+self.p.id+"&room=agent_scratch")
        self.assertEqual(1, len(json.loads(body)["messages"]))
        _, _, body = self.request("/api/message?project="+self.p.id+"&id="+m["event_id"]+"&start=12000")
        self.assertEqual(8007, len(json.loads(body)["body"]))

    def test_installed_skill_cli_join_resume_and_fencing(self):
        run = subprocess.run([sys.executable, "-m", "cenacle", "install-skill", "--dest", str(self.root / "skills")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, run.returncode, run.stderr)
        client = self.root / "skills" / "cenacle" / "scripts" / "cenacle_client.py"
        def cli(*args):
            return subprocess.run([sys.executable, str(client), "--home", str(self.root / "runtime"), *args, "--project", str(self.p.path)], cwd=self.root, capture_output=True, text=True)
        run = cli("join", "--handle", "trial", "--role", "reviewer")
        self.assertEqual(0, run.returncode, run.stderr)
        identity = json.loads(run.stdout)
        agent, session = identity["agent_id"], identity["session_id"]
        self.assertNotIn("credential", identity)
        self.assertTrue((self.root / "runtime" / "sessions" / f"{self.p.id}_{session}.json").exists())
        boot = cli("inbox", "--agent", agent, "--session", session, "--bootstrap")
        self.assertEqual(0, boot.returncode, boot.stderr)
        self.assertIn("general_context", json.loads(boot.stdout))
        resumed = cli("resume", "--agent", agent, "--takeover")
        self.assertEqual(0, resumed.returncode, resumed.stderr)
        old = cli("inbox", "--agent", agent, "--session", session)
        self.assertNotEqual(0, old.returncode)
        self.assertIn("replaced", old.stderr)
        missing = cli("inbox", "--agent", agent)
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("--session", missing.stderr)


if __name__ == "__main__":
    unittest.main()
