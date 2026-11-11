"""Verify admin-only installation, command rewriting and argument forwarding."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SOURCE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallTests(unittest.TestCase):
    def test_standalone_install_has_no_parent_profile_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, HOME=tmp, XDG_CONFIG_HOME=tmp, STANDALONE="1"):
                installer = load_module("install")
                with mock.patch.object(installer.venv, "create"), \
                     mock.patch.object(installer.subprocess, "run"), \
                     mock.patch.object(installer.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}"):
                    installer.install()
            self.assertTrue((Path(tmp) / "dotfiles/claude-admin/.standalone").exists())

    def test_default_merges_existing_settings_once_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            root = home / ".config/dotfiles/claude-admin"
            root.mkdir(parents=True)
            settings_file = home / ".claude/settings.json"
            settings_file.parent.mkdir()
            previous = {
                "theme": "dark",
                "permissions": {"allow": ["Bash(existing *)"], "ask": ["Bash(other *)"]},
                "hooks": {"PreToolUse": [{"matcher": "Read", "hooks": []}]},
            }
            settings_file.write_text(json.dumps(previous))
            added = {"permissions": {"allow": ["Bash(admin-git *)"]},
                     "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]}}
            with mock.patch.dict(os.environ, HOME=tmp):
                installer = load_module("install")
                installer.enable_default(root, added)
                installer.enable_default(root, added)
            current = json.loads(settings_file.read_text())
            self.assertEqual(current["theme"], previous["theme"])
            self.assertEqual(current["permissions"]["ask"], previous["permissions"]["ask"])
            self.assertEqual(current["permissions"]["allow"], ["Bash(existing *)", "Bash(admin-git *)"])
            self.assertEqual(len(current["hooks"]["PreToolUse"]), 2)
            backup, = root.glob("user-settings-backup.*.json")
            self.assertEqual(json.loads(backup.read_text()), previous)

    def test_personal_profile_cannot_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, HOME=tmp, XDG_CONFIG_HOME=tmp):
                with self.assertRaisesRegex(RuntimeError, "会社用 profile"):
                    load_module("install").install()
            self.assertFalse((Path(tmp) / "dotfiles/claude-admin").exists())

    def test_install_generates_only_opt_in_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / ".config"
            profile = config / "dotfiles/profile"
            profile.parent.mkdir(parents=True)
            profile.write_text("work/laptop")
            with mock.patch.dict(os.environ, HOME=tmp, XDG_CONFIG_HOME=str(config)):
                installer = load_module("install")
                with mock.patch.object(installer.venv, "create"), \
                     mock.patch.object(installer.subprocess, "run") as run, \
                     mock.patch.object(installer.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}"):
                    installer.install()
            root = profile.parent / "claude-admin"
            settings = json.loads((root / "settings.json").read_text())
            self.assertEqual(len(settings["permissions"]["allow"]), 2)
            self.assertEqual(list(settings["hooks"]), ["PreToolUse"])
            self.assertIn("--require-hashes", run.call_args.args[0])
            self.assertTrue((Path(tmp) / ".local/bin/claude-admin").is_file())
            self.assertFalse((Path(tmp) / ".claude").exists())

    def test_wrapper_forwards_literal_arguments_and_exit_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dotfiles/claude-admin"
            (root / "bin").mkdir(parents=True)
            (root.parent / "profile").write_text("work")
            tool = root / "fake-tool"
            tool.write_text(f"#!{sys.executable}\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(23)\n")
            tool.chmod(0o700)
            (root / "tools.json").write_text(json.dumps({"git": str(tool), "docker": str(tool)}))
            arguments = ["config", "value with spaces", "$(touch unwanted)", ";"]
            for name, prefix in (("admin-git", []), ("admin-compose", ["compose"])):
                wrapper = root / "bin" / name
                wrapper.write_text((SOURCE / "admin-tool.py").read_text())
                result = subprocess.run([sys.executable, str(wrapper), *arguments], text=True, capture_output=True)
                self.assertEqual(result.returncode, 23, result.stderr)
                self.assertEqual(json.loads(result.stdout), prefix + arguments)
            self.assertFalse((root / "unwanted").exists())


@unittest.skipUnless(importlib.util.find_spec("bashlex"), "Run with the claude-admin .venv Python")
class RewriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module("rewrite")
        cls.root = Path("/company admin")
        cls.git = "'/company admin/bin/admin-git'"
        cls.compose = "'/company admin/bin/admin-compose'"

    def test_preserves_shell_syntax_and_only_changes_executable_words(self):
        cases = [
            ('git -C "some dir" commit -m "git; hello"', f'{self.git} -C "some dir" commit -m "git; hello"'),
            ('docker compose config --services', f'{self.compose}  config --services'),
            ('docker >out compose config', f'{self.compose} >out  config'),
            ('echo "$(git rev-parse HEAD)"', f'echo "$({self.git} rev-parse HEAD)"'),
            ('A=1 /usr/bin/git status > out', f'A=1 {self.git} status > out'),
            ('git status && docker compose ps', f'{self.git} status && {self.compose}  ps'),
            ('echo "git push" # docker compose', 'echo "git push" # docker compose'),
            ('docker ps', 'docker ps'),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(self.module.rewrite(command, self.root)[0], expected)

    def test_unrelated_commands_are_not_auto_approved(self):
        for command in ("git status; npm install", 'echo "$(git status)"'):
            event = {"tool_name": "Bash", "tool_input": {"command": command, "timeout": 123}}
            output = self.module.handle(event, self.root)["hookSpecificOutput"]
            self.assertNotIn("permissionDecision", output)
            self.assertEqual(output["updatedInput"]["timeout"], 123)
        event["tool_input"]["command"] = "git commit -m test"
        self.assertEqual(self.module.handle(event, self.root)["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_unparseable_target_call_is_denied(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "git commit -m '"}}
        self.assertEqual(self.module.handle(event, self.root)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_default_hook_is_inactive_outside_work_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "claude-admin"
            root.mkdir()
            script = root / "rewrite.py"
            script.write_text((SOURCE / "rewrite.py").read_text())
            (root.parent / "profile").write_text("personal")
            event = {"tool_name": "Bash", "tool_input": {"command": "git commit -m test"}}
            result = subprocess.run([sys.executable, str(script)], input=json.dumps(event),
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {})


if __name__ == "__main__":
    unittest.main()
