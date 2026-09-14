import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cenacle.core import Project, Problem, atomic
from cenacle.recovery import memory_dir_path, memory_index_path, recovery_path

ROOT = Path(__file__).resolve().parents[1]


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "Code with spaces Clé"
        self.workspace.mkdir()
        self.p = Project.create(self.workspace / ".cenacle", "Recovery test", "Recover a parser task", self.workspace)
        self.p.set_recovery_home(self.root / "runtime")
        self.a = self.p.command("register", {"handle": "builder"}, human=True)
        self.b = self.p.command("register", {"handle": "reviewer"}, human=True)

    def tearDown(self):
        self.p.close()
        self.temp.cleanup()

    def test_checkpoint_updates_only_own_brief_and_keeps_pending(self):
        other = recovery_path(self.p, self.b["agent_id"]).read_text("utf-8")
        self.p.command("checkpoint", {"body": "Next: validate parser errors", "pending": ["request-1"]}, self.a["credential"])
        result = self.p.command("recovery", {"body": "Next: inspect test_parser.py", "agent_id": self.b["agent_id"]}, self.a["credential"])
        card = Path(result["recovery_file"]).read_text("utf-8")
        self.assertIn("inspect test_parser.py", card)
        self.assertIn("request-1", card)
        self.assertIn("Checkpoint revision: 2", card)
        self.assertIn(str(self.root / "runtime"), card.replace("\\\\", "\\"))
        self.assertEqual(other, recovery_path(self.p, self.b["agent_id"]).read_text("utf-8"))
        with self.assertRaises(Problem):
            self.p.command("checkpoint", {"body": "Human cannot impersonate the agent"}, human=True)

    def test_no_credentials_and_read_order_locators_are_present(self):
        path = recovery_path(self.p, self.a["agent_id"])
        card = path.read_text("utf-8")
        self.assertNotIn(self.a["credential"], card)
        self.assertNotIn(self.b["credential"], card)
        self.assertNotIn("token_hash", card)
        locators = json.loads(card.split("```json\n")[1].split("\n```", 1)[0])
        self.assertEqual(self.a["agent_id"], locators["agent_id"])
        for key in ("skill_file", "client_script", "state_file", "recovery_file", "master_memory", "heartbeat_file"):
            self.assertTrue(Path(locators[key]).is_file(), key)
        self.assertTrue(Path(locators["memory_folder"]).is_dir())
        self.assertEqual(str(self.p.path), locators["project_folder"])
        self.assertIn(self.a["agent_id"], (self.p.path / "RECOVERY.md").read_text("utf-8"))

    def test_agent_owned_master_and_topic_memories_are_preserved_and_indexed(self):
        agent = self.a["agent_id"]
        master = memory_index_path(self.p, agent)
        memory_dir = memory_dir_path(self.p, agent)
        master.write_text("# My memory map\n\n- [Parser decisions](memory/parser-decisions.md)\n", encoding="utf-8")
        topic = memory_dir / "parser-decisions.md"
        topic.write_text("Decision: retain strict UTF-8 parsing. Evidence: test_parser.py.", encoding="utf-8")
        self.p.command("checkpoint", {"body": "Read parser-decisions before editing the parser"}, self.a["credential"])
        card = recovery_path(self.p, agent).read_text("utf-8")
        self.assertIn("parser-decisions.md", card)
        path = self.p.path
        self.p.close()
        self.p = Project(path)
        self.assertIn("My memory map", master.read_text("utf-8"))
        self.assertIn("strict UTF-8", topic.read_text("utf-8"))

    def test_offline_notes_and_handwritten_recovery_survive_restart(self):
        card = recovery_path(self.p, self.a["agent_id"])
        offline = card.with_name("RECOVERY.local.md")
        offline.write_text("Unpublished result: local parser test failed", encoding="utf-8")
        card.write_text("Existing agent-authored recovery note", encoding="utf-8")
        self.p.command("checkpoint", {"body": "Check offline findings"}, self.a["credential"])
        generated = recovery_path(self.p, self.a["agent_id"])
        self.assertEqual("RECOVERY.generated.md", generated.name)
        self.assertIn("Check offline findings", generated.read_text("utf-8"))
        path = self.p.path
        self.p.close()
        self.p = Project(path)
        self.assertEqual("Unpublished result: local parser test failed", offline.read_text("utf-8"))
        self.assertEqual("Existing agent-authored recovery note", card.read_text("utf-8"))
        self.assertIn(generated.name, (self.p.path / "RECOVERY.md").read_text("utf-8"))

    def test_recover_command_works_without_server_and_does_not_resume_identity(self):
        agent = self.a["agent_id"]
        session = self.p.state["agents"][agent]["session_id"]
        self.p.command("checkpoint", {"body": "Next: review the saved parser fixture"}, self.a["credential"])
        self.p.close()
        run = subprocess.run([sys.executable, "-m", "cenacle", "--home", str(self.root / "no-server"), "recover", "--project", str(self.workspace), "--agent", agent], cwd=ROOT, capture_output=True, encoding="utf-8")
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("review the saved parser fixture", run.stdout)
        self.assertIn("context_reset", run.stdout)
        self.p = Project(self.workspace / ".cenacle")
        self.assertEqual(session, self.p.state["agents"][agent]["session_id"])

    def test_failed_recovery_projection_reports_warning_and_repairs_on_retry(self):
        def fail_card(path, value):
            if Path(path).name == "RECOVERY.md":
                raise PermissionError("card locked")
            return atomic(path, value)
        with patch("cenacle.core.atomic", side_effect=fail_card):
            result = self.p.command("checkpoint", {"body": "Committed recovery evidence"}, self.a["credential"], request_id="saved-once")
        self.assertIn("projection_warning", result)
        self.assertEqual("Committed recovery evidence", self.p.state["agents"][self.a["agent_id"]]["checkpoint"])
        result = self.p.command("checkpoint", {"body": "Committed recovery evidence"}, self.a["credential"], request_id="saved-once")
        self.assertNotIn("projection_warning", result)
        self.assertIn("Committed recovery evidence", Path(result["recovery_file"]).read_text("utf-8"))
        self.assertEqual(1, self.p.state["agents"][self.a["agent_id"]]["checkpoint_revision"])

    def test_resume_and_context_reset_keep_emergency_brief_and_cursor(self):
        self.p.command("checkpoint", {"body": "Scoped next action", "pending": ["unfinished"]}, self.a["credential"])
        self.p.command("presence", {"status": "disconnected"}, self.a["credential"])
        fresh = self.p.command("resume", {"agent_id": self.a["agent_id"]}, human=True)
        self.p.command("context_reset", {}, fresh["credential"])
        boot = self.p.inbox(fresh["credential"], bootstrap=True)
        self.assertEqual("Scoped next action", boot["identity"]["checkpoint"])
        self.assertEqual(["unfinished"], boot["identity"]["pending"])
        self.assertIn("Scoped next action", Path(fresh["recovery_file"]).read_text("utf-8"))
