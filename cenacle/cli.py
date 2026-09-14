"""Human setup and agent-neutral JSON client. No model SDK or account required."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
import uuid
import urllib.error
import urllib.request
from pathlib import Path

from .core import Project, Problem, atomic, uid
from .server import home, make_server


def request(endpoint, route, body, credential=None):
    raw = json.dumps(body).encode()
    req = urllib.request.Request(endpoint["url"] + route, data=raw, headers={"Content-Type": "application/json", "Authorization": "Bearer " + (credential or endpoint["credential"])})
    try:
        with urllib.request.urlopen(req, timeout=55) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        with exc:
            detail = json.load(exc)
        raise Problem(detail.get("error", str(exc)), exc.code)
    except urllib.error.URLError as exc:
        raise Problem("Coordinator unavailable. Start 'cenacle serve'; do not repeatedly post presence questions. " + str(exc.reason))


def parser():
    p = argparse.ArgumentParser(prog="cenacle", description="Local conversations for independent agents")
    p.add_argument("--home", help="Local endpoint/credential directory; defaults to ~/.cenacle")
    sub = p.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Start the loopback app; open the printed URL")
    serve.add_argument("--port", type=int, default=4310)
    serve.add_argument("--project")
    serve.add_argument("--browser", action="store_true", help="Open the local UI in your default browser")
    init = sub.add_parser("init", help="Create an empty, paused coordination project")
    init.add_argument("path")
    init.add_argument("--name", required=True)
    init.add_argument("--goal", required=True)
    init.add_argument("--workspace", required=True)
    init.add_argument("--human", default="Human")
    init.add_argument("--context-file")
    init.add_argument("--reference", default="")
    install = sub.add_parser("install-skill", help="Copy the portable skill to a chosen skills directory")
    install.add_argument("--dest", required=True, help="Parent skills directory, e.g. .agents/skills or .claude/skills")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--project")
    recover = sub.add_parser("recover", help="Read the project/agent recovery file, even when the coordinator is offline")
    recover.add_argument("--project", required=True, help="Coordination folder or workspace containing .cenacle")
    recover.add_argument("--agent", help="Your immutable agent UUID; omit to read the identity index")
    for name in ("open", "join", "resume", "inbox", "watch", "fetch", "inspect", "call"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--project", required=True, help="Coordination folder or project UUID")
        if name not in ("open", "join", "resume"):
            cmd.add_argument("--agent", help="Agent UUID; required except human administrative calls")
            cmd.add_argument("--session", help="Session UUID returned by join/resume; fences old terminals")
        if name == "join":
            cmd.add_argument("--handle", required=True)
            cmd.add_argument("--role", default="contributor")
            cmd.add_argument("--provider", default="other")
        if name == "resume":
            cmd.add_argument("--agent", required=True)
            cmd.add_argument("--takeover", action="store_true")
        if name == "inbox":
            cmd.add_argument("--bootstrap", action="store_true")
            cmd.add_argument("--max-bytes", type=int)
        if name == "watch":
            cmd.add_argument("--after", type=int, required=True)
            cmd.add_argument("--timeout", type=float, default=30)
        if name == "fetch":
            cmd.add_argument("--message", required=True)
            cmd.add_argument("--start", type=int, default=0)
            cmd.add_argument("--length", type=int, default=3000)
        if name == "inspect":
            cmd.add_argument("kind", choices=["agents", "rooms", "tasks", "votes", "decisions", "messages"])
            cmd.add_argument("--key")
            cmd.add_argument("--start", type=int, default=0)
            cmd.add_argument("--limit", type=int, default=10)
            cmd.add_argument("--query", default="")
        if name == "call":
            cmd.add_argument("action")
            cmd.add_argument("--json", default="{}", help="JSON object; --data-file avoids shell quoting")
            cmd.add_argument("--data-file")
            cmd.add_argument("--body-file", help="Read a message/checkpoint/decision body from this UTF-8 file")
            cmd.add_argument("--request-id", help="Reuse this ID when retrying a mutation")
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    if args.home:
        os.environ["CENACLE_HOME"] = str(Path(args.home).resolve())
    try:
        if args.command == "serve":
            server = make_server(args.port)
            if args.project:
                server.app.open(args.project)
            print(f"Cenacle is ready: http://127.0.0.1:{server.server_address[1]}\nKeep this process running. Ctrl+C stops the coordinator, not your agent terminals.", flush=True)
            if args.browser:
                import webbrowser
                webbrowser.open(f"http://127.0.0.1:{server.server_address[1]}")
            try:
                server.serve_forever(poll_interval=.5)
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
                server.app.close()
            return
        if args.command == "init":
            context = Path(args.context_file).read_text("utf-8") if args.context_file else ""
            p = Project.create(args.path, args.name, args.goal, args.workspace, args.human, args.reference, context)
            result = {"project_id": p.id, "path": str(p.path), "config": str(p.path / "cenacle.json"), "paused": True}
            p.close()
        elif args.command == "recover":
            root = Path(args.project).expanduser().resolve()
            if not (root / "cenacle.json").is_file() and (root / ".cenacle" / "cenacle.json").is_file():
                root = root / ".cenacle"
            config = json.loads((root / "cenacle.json").read_text("utf-8"))
            folder = root
            if args.agent:
                uuid.UUID(args.agent)
                if not any(a["id"] == args.agent for a in config["agents"]):
                    raise Problem("This agent UUID is not in the project's roster")
                folder = root / "cenacle_files" / "agents" / args.agent
            path = folder / "RECOVERY.generated.md"
            if not path.is_file():
                path = folder / "RECOVERY.md"
            if not path.is_file():
                raise Problem("Recovery file not generated yet. Open this project with the updated coordinator first.")
            print(path.read_text("utf-8"))
            return
        elif args.command == "install-skill":
            target = Path(args.dest).expanduser().resolve() / "cenacle"
            if target.exists():
                raise Problem("Skill already exists at destination; inspect it before replacing")
            shutil.copytree(Path(__file__).parent / "skills" / "cenacle", target)
            # The standalone launcher resolves the installed app without depending on host CWD.
            atomic(target / "scripts" / "app.json", {"python": sys.executable, "app_root": str(Path(__file__).parent.parent)})
            result = {"installed": str(target)}
        else:
            try:
                endpoint = json.loads((home() / "endpoint.json").read_text("utf-8"))
            except (OSError, ValueError):
                raise Problem("Start 'python -m cenacle serve' first (or use the same --home as the server)")
            project_arg = getattr(args, "project", None)
            if args.command == "doctor" and not project_arg:
                result = {"endpoint": endpoint["url"], "python": sys.executable, "version": "0.1.0", "credential_directory": str(home()), "note": "Use --project to verify the connection and project."}
            else:
                if not project_arg:
                    raise Problem("A project is required")
                if Path(project_arg).is_dir():
                    pid = request(endpoint, "/api/open", {"path": str(Path(project_arg).resolve())})["project"]
                else:
                    pid = project_arg
                agent_id = getattr(args, "agent", None)
                credential = None
                if agent_id and args.command != "resume":
                    if not getattr(args, "session", None):
                        raise Problem("Include --session with the session_id returned by join/resume")
                    try:
                        session = json.loads((home() / "sessions" / f"{pid}_{args.session}.json").read_text("utf-8"))
                    except (OSError, ValueError):
                        raise Problem("No local session credential. Resume this identity first.")
                    if session["agent_id"] != agent_id:
                        raise Problem("Session does not belong to this agent")
                    credential = session["credential"]
                base = {"project": pid}
                if args.command in ("open", "doctor"):
                    result = {"project_id": pid, "url": endpoint["url"], "connected": True}
                elif args.command in ("join", "resume"):
                    data = {"handle": args.handle, "role": args.role, "provider": args.provider} if args.command == "join" else {"agent_id": args.agent, "takeover": args.takeover}
                    result = request(endpoint, "/api/command", {**base, "action": "register" if args.command == "join" else "resume", "args": data, "request_id": uid()})
                    atomic(home() / "sessions" / f'{pid}_{result["session_id"]}.json', {"project": pid, **result})
                    result.pop("credential", None)
                    result["coordinator_home"] = str(home())
                    result["next"] = "inbox --bootstrap; read general_context and controls before work"
                elif args.command == "inbox":
                    if not credential:
                        raise Problem("inbox requires --agent")
                    result = request(endpoint, "/api/inbox", {**base, "bootstrap": args.bootstrap, "max_bytes": args.max_bytes}, credential)
                elif args.command == "watch":
                    if not credential:
                        raise Problem("watch requires --agent")
                    result = request(endpoint, "/api/watch", {**base, "after": args.after, "timeout": args.timeout}, credential)
                elif args.command == "fetch":
                    if not credential:
                        raise Problem("fetch requires --agent and --session")
                    result = request(endpoint, "/api/fetch", {**base, "message_id": args.message, "start": args.start, "length": args.length}, credential)
                elif args.command == "inspect":
                    if not credential:
                        raise Problem("inspect requires --agent and --session")
                    result = request(endpoint, "/api/inspect", {**base, "kind": args.kind, "key": args.key, "start": args.start, "limit": args.limit, "query": args.query}, credential)
                elif args.command == "call":
                    data = json.loads(Path(args.data_file).read_text("utf-8") if args.data_file else args.json)
                    if args.body_file:
                        data["body"] = Path(args.body_file).read_text("utf-8")
                    result = request(endpoint, "/api/command", {**base, "action": args.action, "args": data, "request_id": args.request_id or uid()}, credential)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (Problem, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
