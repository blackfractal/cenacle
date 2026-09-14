import json
from pathlib import Path
from subprocess import CompletedProcess
import tempfile
import unittest
from unittest.mock import patch

from cenacle.folder_picker import choose_folder, PickerError


class FolderPickerTests(unittest.TestCase):
    def test_nonexistent_coordination_path_survives_native_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "Clé with spaces" / ".cenacle"
            output = CompletedProcess([], 0, json.dumps({"path": str(target)}), "")
            with patch("cenacle.folder_picker.subprocess.run", return_value=output) as child:
                self.assertEqual(str(target), choose_folder(str(target.parent), "New room", allow_new=True))
                self.assertTrue(json.loads(child.call_args.kwargs["input"])["allow_new"])
            self.assertFalse(target.exists())
            with patch("cenacle.folder_picker.subprocess.run", return_value=output):
                with self.assertRaises(PickerError):
                    choose_folder(str(target.parent), "Existing workspace")

    def test_files_are_not_accepted_as_new_folders(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "code.py"
            target.write_text("# code", encoding="utf-8")
            output = CompletedProcess([], 0, json.dumps({"path": str(target)}), "")
            with patch("cenacle.folder_picker.subprocess.run", return_value=output):
                with self.assertRaises(PickerError):
                    choose_folder(allow_new=True)
