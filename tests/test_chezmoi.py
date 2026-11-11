"""Exercise chezmoi itself against disposable HOME directories."""
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ChezmoiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home),
                        XDG_CONFIG_HOME=str(self.home / '.config'),
                        XDG_DATA_HOME=str(self.home / '.local/share'),
                        XDG_CACHE_HOME=str(self.home / '.cache'))

    def run_chezmoi(self, *args, os_name=None, check=True):
        command = ['chezmoi', '--source', str(ROOT), '--destination', str(self.home)]
        if os_name:
            command += ['--override-data', json.dumps({'chezmoi': {'os': os_name}})]
        return subprocess.run(command + list(args), env=self.env, text=True,
                              capture_output=True, check=check)

    def test_platform_selection(self):
        for os_name, included, excluded in (
            ('darwin', '.config/karabiner/karabiner.json', '.config/hypr/hypridle.conf'),
            ('linux', '.config/hypr/hypridle.conf', '.config/karabiner/karabiner.json'),
            ('windows', '.config/windows/desired-state.json', '.config/omarchy/hooks/post-boot.d/00-idle-off'),
        ):
            with self.subTest(os=os_name):
                entries = self.run_chezmoi('managed', '--include', 'files', os_name=os_name).stdout.splitlines()
                self.assertIn(included, entries)
                self.assertNotIn(excluded, entries)
                self.assertNotIn('.config/claude-code/env.example', entries)

    def test_apply_twice_is_unchanged_and_local_drift_is_detected(self):
        self.run_chezmoi('init', '--apply')
        target = self.home / '.config/zeno/config.yml'
        modified = target.stat().st_mtime_ns
        self.run_chezmoi('apply')
        self.assertEqual(target.stat().st_mtime_ns, modified)
        self.assertEqual(self.run_chezmoi('diff').stdout, '')
        self.run_chezmoi('verify')
        target.write_text('local edit\n')
        self.assertNotEqual(self.run_chezmoi('verify', check=False).returncode, 0)
        diagnostic = subprocess.run(['make', 'verify', f'HOME={self.home}'], cwd=ROOT,
                                    env=self.env, text=True, capture_output=True)
        self.assertNotEqual(diagnostic.returncode, 0)
        self.assertIn('local edit', diagnostic.stdout)
        self.assertIn('config.yml', diagnostic.stdout)
        self.assertIn('make apply-files', diagnostic.stderr)
        self.assertEqual(target.read_text(), 'local edit\n')
        result = self.run_chezmoi('--error-on-conflict', 'apply', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), 'local edit\n')
        self.assertFalse(target.with_name('config.yml.backup').exists())

    def test_dry_run_does_not_apply_or_backup_existing_files(self):
        target = self.home / '.zshrc'
        target.write_text('personal shell\n')
        self.run_chezmoi('--dry-run', 'apply')
        self.assertEqual(target.read_text(), 'personal shell\n')
        self.assertFalse((self.home / '.zshrc.backup').exists())
        self.assertFalse((self.home / '.config/zeno/config.yml').exists())

    def test_directory_symlink_migration_preserves_unmanaged_files(self):
        external = Path(self.temp.name) / 'external'
        (external / 'zeno').mkdir(parents=True)
        (external / 'zeno/config.yml').write_text('old managed config\n')
        (external / 'private.txt').write_text('unmanaged\n')
        (self.home / '.config').symlink_to(external)
        self.run_chezmoi('apply')
        self.assertFalse((self.home / '.config').is_symlink())
        self.assertEqual((external / 'zeno/config.yml').read_text(), 'old managed config\n')
        self.assertEqual((self.home / '.config/private.txt').read_text(), 'unmanaged\n')
        self.assertTrue((self.home / '.config.backup').is_symlink())
        self.assertEqual((self.home / '.config/zeno/config.yml.backup').read_text(), 'old managed config\n')

    def test_linux_hook_remains_executable(self):
        self.run_chezmoi('apply', os_name='linux')
        hook = self.home / '.config/omarchy/hooks/post-boot.d/00-idle-off'
        self.assertTrue(os.access(hook, os.X_OK))
        self.assertTrue(os.access(self.home / '.config/ranger/scope.sh', os.X_OK))
        self.assertFalse((self.home / '.config/karabiner').exists())

    def test_first_targeted_apply_does_not_remove_other_targets(self):
        shell = self.home / '.zshrc'
        shell.write_text('personal shell\n')
        self.run_chezmoi('apply', '--parent-dirs', str(self.home / '.config/zeno/config.yml'))
        self.assertEqual(shell.read_text(), 'personal shell\n')
        self.assertFalse((self.home / '.zshrc.backup').exists())
        self.run_chezmoi('apply')
        self.assertEqual((self.home / '.zshrc.backup').read_text(), 'personal shell\n')

    def test_compatibility_entrypoint_does_not_init_into_external_config(self):
        external = Path(self.temp.name) / 'external'
        external.mkdir()
        (external / 'private.txt').write_text('unmanaged\n')
        (self.home / '.config').symlink_to(external)
        subprocess.run(['bash', str(ROOT / 'scripts/link.sh')], env=self.env,
                       check=True, capture_output=True)
        self.assertEqual(sorted(p.name for p in external.iterdir()), ['private.txt'])
        self.assertTrue((self.home / '.config/chezmoi/chezmoi.toml').is_file())

    def test_moving_checkout_does_not_rerun_migration(self):
        shell = self.home / '.zshrc'
        shell.write_text('personal shell\n')
        old = Path(self.temp.name) / 'old-checkout'
        new = Path(self.temp.name) / 'ghq/github.com/user/dotfiles'
        for checkout in (old, new):
            shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns('.git', '.validation'))
        for checkout in (old, new):
            subprocess.run(['chezmoi', '--source', str(checkout), '--destination', str(self.home),
                            'apply'], env=self.env, check=True, capture_output=True, text=True)
        self.assertEqual((self.home / '.zshrc.backup').read_text(), 'personal shell\n')
        backups = sorted(str(p.relative_to(self.home)) for p in self.home.rglob('*.backup*'))
        self.assertEqual(backups, ['.zshrc.backup'])
        self.assertIn(str(new), shell.read_text())

    def test_checkout_path_is_quoted_in_shell_entrypoint(self):
        source = Path(self.temp.name) / 'checkout with $literal'
        shutil.copytree(ROOT / 'home', source / 'home')
        shutil.copytree(ROOT / 'modules', source / 'modules')
        shutil.copy(ROOT / '.chezmoiroot', source / '.chezmoiroot')
        module = source / 'modules/shell-environment/scripts/common/.zshrc'
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text('DOTFILES_SOURCED=1\n')
        for name in ('macos/brew.zsh', 'linux/yay.zsh'):
            stub = source / 'scripts' / name
            stub.parent.mkdir(parents=True, exist_ok=True)
            stub.write_text('')
        subprocess.run(['chezmoi', '--source', str(source), '--destination', str(self.home), 'apply'],
                       env=self.env, check=True, capture_output=True)
        subprocess.run(['zsh', '-f', '-c', 'source "$HOME/.zshrc"; [[ $DOTFILES_SOURCED == 1 ]]'],
                       env=self.env, check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
