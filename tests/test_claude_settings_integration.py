"""Both independently distributed Claude modules must preserve concurrent updates."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClaudeSettingsIntegrationTests(unittest.TestCase):
    def test_concurrent_module_updates_keep_both_owners_and_user_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home / ".claude/settings.json"
            target.parent.mkdir()
            target.write_text('{"customUserPreference":"keep"}')
            backup = home / "work-backups"
            backup.mkdir()
            install = ROOT / "modules/claude-work-tools/scripts/install.py"
            status = ROOT / "modules/claude-statusline/scripts/settings.py"
            code = (
                "import importlib.util,sys; from pathlib import Path; "
                "spec=importlib.util.spec_from_file_location('work_install',sys.argv[1]); "
                "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                "module.enable_default(Path(sys.argv[2]),"
                "{'permissions':{'allow':['Bash(admin-git *)']},"
                "'hooks':{'PreToolUse':[{'matcher':'Bash','hooks':[]}]}})"
            )
            env = dict(os.environ, HOME=directory, XDG_STATE_HOME=str(home / "state"))
            processes = []
            for _ in range(4):
                processes.append(subprocess.Popen([sys.executable, "-c", code, str(install), str(backup)],
                                                  env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
                processes.append(subprocess.Popen([sys.executable, str(status)], env=env,
                                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE))
            for process in processes:
                stdout, stderr = process.communicate(timeout=20)
                self.assertEqual(process.returncode, 0, stderr.decode())
            data = json.loads(target.read_text())
            self.assertEqual(data["customUserPreference"], "keep")
            self.assertEqual(data["permissions"]["allow"], ["Bash(admin-git *)"])
            self.assertEqual(len(data["hooks"]["PreToolUse"]), 1)
            self.assertEqual(data["statusLine"]["command"], "~/.claude/statusline.sh")
            self.assertEqual(data["theme"], "auto")
