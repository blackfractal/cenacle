"""Native folder dialog in its own process so Tk stays on a main thread."""
from pathlib import Path
import json
import os
import subprocess
import sys


class PickerError(Exception):
    pass


def choose_folder(initial="", title="Choose a folder", allow_new=False):
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve())],
            input=json.dumps({"initial": initial, "title": title, "allow_new": allow_new}),
            capture_output=True, text=True, encoding="utf-8", timeout=600,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        payload = json.loads(result.stdout)
        if result.returncode or payload.get("error"):
            raise PickerError(payload.get("error", "The folder picker could not open."))
        selected = payload.get("path")
        if selected and (Path(selected).exists() and not Path(selected).is_dir() or not allow_new and not Path(selected).is_dir()):
            raise PickerError("The selected folder is no longer available.")
        return str(Path(selected).resolve()) if selected else None
    except subprocess.TimeoutExpired:
        raise PickerError("The folder picker timed out. Click Browse to try again.") from None
    except (OSError, ValueError) as exc:
        raise PickerError("Unable to open the folder picker. You can still enter a folder path.") from exc


def main():
    root = None
    try:
        import tkinter as tk
        from tkinter import filedialog
        args = json.load(sys.stdin)
        initial = Path(args.get("initial") or Path.home()).expanduser().resolve()
        while not initial.is_dir() and initial != initial.parent:
            initial = initial.parent
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(parent=root, title=args["title"],
                                            initialdir=str(initial), mustexist=not args.get("allow_new", False))
        print(json.dumps({"path": selected or None}))
    except Exception:
        print(json.dumps({"error": "The native folder picker is unavailable. Install Python with Tcl/Tk support, or enter the folder path manually."}))
        return 1
    finally:
        if root is not None:
            root.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
