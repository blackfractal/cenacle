"""Host-neutral launcher; installed copies remember where the app is installed."""
from pathlib import Path
import json
import subprocess
import sys

config = Path(__file__).with_name("app.json")
if config.exists():
    settings = json.loads(config.read_text("utf-8"))
    root = Path(settings["app_root"])
    python = settings["python"]
else:
    # Source checkout: cenacle/skills/cenacle/scripts/cenacle_client.py
    root = Path(__file__).resolve().parents[4]
    python = sys.executable
if not (root / "cenacle" / "__main__.py").is_file():
    sys.exit("Cenacle application moved or is unavailable. Reinstall the skill from the application.")
# Preserve caller CWD so relative project/body/workspace paths have their usual meaning.
code = "import sys; sys.path.insert(0, sys.argv.pop(1)); from cenacle.cli import main; main()"
raise SystemExit(subprocess.call([python, "-c", code, str(root), *sys.argv[1:]]))
