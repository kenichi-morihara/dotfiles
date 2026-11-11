"""Status preferences preserve separately registered hooks and other user settings."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts/settings.py"
spec = importlib.util.spec_from_file_location("statusline_settings", SOURCE)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class SettingsTests(unittest.TestCase):
    def test_merge_preserves_permissions_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home / ".claude/settings.json"
            target.parent.mkdir()
            original = {"permissions": {"allow": ["Bash(existing *)"]}, "hooks": {"PreToolUse": []}}
            target.write_text(json.dumps(original))
            with patch.dict(os.environ, HOME=directory, XDG_STATE_HOME=str(home / "state")):
                self.assertEqual(settings.update(check=True), 1)
                settings.update()
                modified = target.stat().st_mtime_ns
                settings.update()
                self.assertEqual(target.stat().st_mtime_ns, modified)
                self.assertEqual(settings.update(check=True), 0)
            current = json.loads(target.read_text())
            self.assertEqual(current["permissions"], original["permissions"])
            self.assertEqual(current["hooks"], original["hooks"])
            backup, = (home / "state/claude-statusline/backups").glob("*.json")
            self.assertEqual(json.loads(backup.read_text()), original)
