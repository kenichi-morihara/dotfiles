"""Profiles run against disposable homes and command stubs, never real services."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'scripts/common/profiles.py'
spec = importlib.util.spec_from_file_location('profiles', TOOL)
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = dict(os.environ, HOME=str(self.home),
                        XDG_CONFIG_HOME=str(self.home / '.config'),
                        XDG_DATA_HOME=str(self.home / '.local/share'),
                        XDG_CACHE_HOME=str(self.home / '.cache'))
        self.environment = patch.dict(os.environ, self.env)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def cli(self, *args, check=True):
        return subprocess.run([sys.executable, str(TOOL), *args],
                              env=self.env, capture_output=True, text=True, check=check)

    def stub(self, name, body):
        directory = self.home / 'bin'
        directory.mkdir(exist_ok=True)
        command = directory / name
        command.write_text('#!/bin/sh\n' + body + '\n')
        command.chmod(0o755)
        self.env['PATH'] = str(directory) + ':' + os.environ['PATH']
        os.environ['PATH'] = self.env['PATH']
        return command

    def test_selection_show_and_preview_have_no_install_side_effects(self):
        self.stub('ghq', 'exit 99')
        self.cli('select', '--name', 'personal')
        state = profiles.selection_path()
        before = {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        data = json.loads(self.cli('show').stdout)
        self.assertEqual(data['package_profile'], 'full')
        self.assertEqual(len(data['repos']), 3)
        self.cli('plan')
        after = {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(state.read_text(), 'personal\n')

    def test_interactive_select_creates_machine_profile(self):
        answers = iter(['3', 'zz-test-mac'])
        machine = profiles.ROOT / 'profiles/work/zz-test-mac.toml'
        self.addCleanup(machine.unlink, missing_ok=True)
        with patch.object(profiles, 'interactive', return_value=True), \
                patch('builtins.input', lambda prompt='': next(answers)), \
                patch.object(sys, 'argv', ['profiles.py', 'select']):
            self.assertEqual(profiles.main(), 0)
        self.assertEqual(profiles.selection_path().read_text(), 'work/zz-test-mac\n')
        self.assertEqual(machine.read_text(), (profiles.ROOT / 'profiles/work/example.toml').read_text())

    def test_invalid_or_missing_selection_cannot_start_setup(self):
        for name in ('../personal', 'work/../../x', 'work/example', 'work/missing'):
            self.assertNotEqual(self.cli('select', '--name', name, check=False).returncode, 0)
        self.assertFalse(profiles.selection_path().exists())
        self.assertNotEqual(self.cli('setup', check=False).returncode, 0)

    def test_work_defaults_and_machine_overrides_replace_lists(self):
        copy = self.home / 'source'
        shutil.copytree(ROOT / 'profiles', copy / 'profiles')
        (copy / 'profiles/work/laptop.toml').write_text(
            'packages = ["jq"]\nkeyboard_layout = "jis"\nrepos = ["example.com/team/repo"]\n')
        with patch.object(profiles, 'ROOT', copy):
            work = profiles.resolve('work')
            self.assertEqual(work['repos'], [])
            self.assertEqual(work['package_profile'], 'core')
            self.assertEqual(work['keyboard_layout'], 'us')
            machine = profiles.resolve('work/laptop')
            self.assertEqual(machine['packages'], ['jq'])
            self.assertEqual(machine['repos'], ['example.com/team/repo'])
            self.assertEqual(machine['keyboard_layout'], 'jis')
            (copy / 'profiles/work/laptop.toml').write_text('packages = "bad"\n')
            with self.assertRaises(ValueError):
                profiles.resolve('work/laptop')

    def test_existing_checkout_is_used_without_get_or_pull(self):
        checkout = self.home / 'custom-ghq/github.com/kenichi-morihara/mac-security-audit'
        checkout.mkdir(parents=True)
        self.stub('ghq', f'if [ "$1" = list ]; then echo "{checkout}"; else exit 99; fi')
        profiles.prepare_repo('github.com/kenichi-morihara/mac-security-audit', [])

    def test_checkout_get_and_failure_stop_before_dependencies(self):
        checkout = self.home / 'ghq/example.com/team/repo'
        marker = self.home / 'get'
        self.stub('ghq', f'''if [ "$1" = list ]; then
  [ ! -f "{marker}" ] || echo "{checkout}"
  exit 0
fi
[ "$1" = get ] || exit 99
mkdir -p "{checkout}"
touch "{marker}"''')
        profiles.prepare_repo('example.com/team/repo', [])
        self.assertTrue(marker.exists())
        self.stub('ghq', 'if [ "$1" = list ]; then exit 0; else exit 23; fi')
        with self.assertRaises(subprocess.CalledProcessError):
            profiles.prepare_repo('example.com/team/failed', [])

    def test_dependency_retry_uses_existing_environment_and_stops_on_failure(self):
        checkout = self.home / 'ghq/github.com/kenichi-morihara/personal-knowledge'
        python = checkout / '.venv/bin/python'
        python.parent.mkdir(parents=True)
        log = self.home / 'pip.log'
        python.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\nexit "${{PIP_STUB_STATUS:-0}}"\n')
        python.chmod(0o755)
        self.stub('ghq', f'if [ "$1" = list ]; then echo "{checkout}"; else exit 99; fi')
        repo = 'github.com/kenichi-morihara/personal-knowledge'
        profiles.prepare_repo(repo, [])
        profiles.prepare_repo(repo, ['capture'])
        self.assertEqual(log.read_text().splitlines(), [
            '-m pip install -r requirements-mcp.txt',
            '-m pip install -r requirements-mcp.txt',
            '-m pip install -r requirements-capture.txt'])
        with patch.dict(os.environ, PIP_STUB_STATUS='24'):
            with self.assertRaises(subprocess.CalledProcessError):
                profiles.prepare_repo(repo, ['ledger'])
        self.assertNotIn('ledger', log.read_text())

    def test_personal_ops_uses_mise_and_dependency_failure_is_propagated(self):
        checkout = self.home / 'ghq/github.com/kenichi-morihara/personal-ops'
        (checkout / 'ai-tasks').mkdir(parents=True)
        self.stub('ghq', f'if [ "$1" = list ]; then echo "{checkout}"; else exit 99; fi')
        log = self.home / 'npm.log'
        self.stub('mise', f'echo "$PWD: $*" >> "{log}"\nexit 21')
        with self.assertRaises(subprocess.CalledProcessError):
            profiles.prepare_repo('github.com/kenichi-morihara/personal-ops', [])
        self.assertEqual(log.read_text(), str((checkout / 'ai-tasks').resolve()) + ': exec -- npm ci\n')

    def test_setup_orders_stages_and_propagates_package_failure(self):
        config = profiles.resolve('work')
        with patch.object(profiles.platform, 'system', return_value='Darwin'), patch.object(profiles, 'run') as run:
            profiles.execute(config, 'setup')
            self.assertEqual([c.args[0] for c in run.call_args_list], [
                ['bash', 'scripts/macos/brew.sh', '--profile', 'core'],
                ['make', 'init'], ['make', 'apply'], ['make', 'runtimes']])
            run.reset_mock()
            run.side_effect = subprocess.CalledProcessError(1, 'brew')
            with self.assertRaises(subprocess.CalledProcessError):
                profiles.execute(config, 'setup')
            self.assertEqual(run.call_count, 1)

    def test_brew_wrapper_skips_dump_and_git_for_selected_work_machine(self):
        self.cli('select', '--name', 'work')
        log = self.home / 'brew.log'
        self.stub('brew', f'echo "$@" >> "{log}"')
        self.stub('git', 'exit 99')
        subprocess.run(['zsh', '-f', '-c', 'source "$1"; brew install example',
                        'test', str(ROOT / 'scripts/macos/brew.zsh')],
                       env=self.env, check=True, capture_output=True)
        self.assertEqual(log.read_text(), 'install example\n')

    @unittest.skipUnless(sys.platform == 'darwin', 'profile Homebrew integration is macOS only')
    def test_make_packages_legacy_default_and_explicit_override(self):
        self.stub('uname', 'echo Darwin')
        self.stub('brew', 'printf "%s\\n" "$@"')
        def make(*args):
            return subprocess.run(['make', '-C', str(ROOT), *args], env=self.env,
                                  check=True, text=True, capture_output=True).stdout
        self.assertIn('.Brewfile.core', make('packages'))
        self.cli('select', '--name', 'personal')
        self.assertIn('--file=' + str(ROOT / 'scripts/macos/.Brewfile') + '\n', make('packages-check'))
        self.assertIn('.Brewfile.core', make('packages', 'PROFILE=core'))

    @unittest.skipUnless(shutil.which('chezmoi'), 'chezmoi required')
    def test_chezmoi_work_default_and_explicit_keyboard_survive_reinit(self):
        self.cli('select', '--name', 'work')
        command = ['chezmoi', '--source', str(ROOT), '--destination', str(self.home),
                   '--override-data', '{"chezmoi":{"os":"darwin"}}']
        def apply():
            subprocess.run(command + ['init', '--apply'], env=self.env,
                           check=True, capture_output=True)
            data = json.loads((self.home / '.config/karabiner/karabiner.json').read_text())
            return next(p for p in data['profiles'] if p.get('selected'))
        self.assertEqual(apply()['virtual_hid_keyboard']['keyboard_type_v2'], 'ansi')
        self.assertEqual(apply()['virtual_hid_keyboard']['keyboard_type_v2'], 'ansi')
        self.cli('select', '--name', 'personal')
        self.assertEqual(apply()['virtual_hid_keyboard']['keyboard_type_v2'], 'jis')
        self.cli('select', '--name', 'work')
        self.assertEqual(apply()['virtual_hid_keyboard']['keyboard_type_v2'], 'ansi')
        config = self.home / '.config/chezmoi/chezmoi.toml'
        config.write_text(config.read_text() + 'keyboardLayout = "jis"\n')
        self.assertEqual(apply()['virtual_hid_keyboard']['keyboard_type_v2'], 'jis')
        self.assertIn('keyboardLayout = "jis"', config.read_text())
        self.cli('select', '--name', 'personal')
        self.assertEqual(apply()['virtual_hid_keyboard']['keyboard_type_v2'], 'jis')


if __name__ == '__main__':
    unittest.main()
