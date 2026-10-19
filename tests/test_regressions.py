"""Exercise setup failure paths using disposable homes and fake commands."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LinkBackupTests(unittest.TestCase):
    def test_existing_backups_and_dangling_links_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            missing = home / 'missing-original'
            (home / '.zshrc').symlink_to(missing)
            (home / '.zshrc.backup').write_text('first backup')
            (home / '.zshrc.backup.1').symlink_to(home / 'missing-backup')
            for _ in range(2):
                subprocess.run(['bash', str(ROOT / '.bin/link.sh')],
                               env=dict(os.environ, HOME=tmp),
                               check=True, capture_output=True)
            self.assertEqual((home / '.zshrc').resolve(), ROOT / '.bin/common/.zshrc')
            self.assertEqual((home / '.zshrc.backup').read_text(), 'first backup')
            self.assertEqual(os.readlink(home / '.zshrc.backup.1'), str(home / 'missing-backup'))
            self.assertEqual(os.readlink(home / '.zshrc.backup.2'), str(missing))
            self.assertFalse((home / '.zshrc.backup.3').is_symlink())
            self.assertFalse((home / '.zshrc.backup.3').exists())


class BrewBundleFailureTests(unittest.TestCase):
    def run_bundle(self, *args, platform='Darwin', brew_status=0):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            log = directory / 'brew-called'
            for name, body in (
                ('uname', f'echo {platform}'),
                ('brew', f'echo called > "$BREW_CALL_LOG"\nexit {brew_status}'),
            ):
                command = directory / name
                command.write_text('#!/bin/sh\n' + body + '\n')
                command.chmod(0o755)
            result = subprocess.run(
                ['bash', str(ROOT / '.bin/macos/brew.sh'), *args],
                env=dict(os.environ, HOME=tmp, PATH=tmp + ':' + os.environ['PATH'],
                         BREW_CALL_LOG=str(log)),
                text=True, capture_output=True,
            )
            return result, log.exists()

    def test_unknown_profile_does_not_invoke_brew(self):
        result, called = self.run_bundle('--profile', 'unknown')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Unknown profile', result.stderr)
        self.assertFalse(called)

    def test_missing_profile_does_not_invoke_brew(self):
        result, called = self.run_bundle('--profile')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Usage:', result.stderr)
        self.assertFalse(called)

    def test_non_macos_does_not_invoke_brew(self):
        result, called = self.run_bundle(platform='Linux')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Not macOS!', result.stdout)
        self.assertFalse(called)

    def test_bundle_failure_is_propagated(self):
        result, called = self.run_bundle('check', brew_status=42)
        self.assertTrue(called)
        self.assertEqual(result.returncode, 42)


if __name__ == '__main__':
    unittest.main()
