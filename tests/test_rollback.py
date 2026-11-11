import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / 'scripts/common/rollback.py'


class RollbackTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.env = {**os.environ, 'HOME': str(self.home)}
        self.chezmoi = self.script('chezmoi', '''
printf '%s\\0' '.zshrc' '.config' '.config/with space' '.config/link'
''')
        self.make = self.script('make', '''
printf 'applied' > "$HOME/.zshrc"
chmod 644 "$HOME/.zshrc"
mkdir -p "$HOME/.config"
printf 'new' > "$HOME/.config/with space"
ln -s missing "$HOME/.config/link"
exit "${FAKE_MAKE_STATUS:-0}"
''')
        self.zshrc = self.home / '.zshrc'
        self.zshrc.write_text('personal')
        self.zshrc.chmod(0o600)
        self.sessions = self.home / '.local/state/dotfiles/rollback'

    def script(self, name, body):
        path = self.root / name
        path.write_text('#!/bin/sh\nset -eu\n' + body)
        path.chmod(0o700)
        return path

    def run_tool(self, *args, expected=0):
        result = subprocess.run([sys.executable, '-B', str(TOOL), *map(str, args)],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def track(self, expected=0):
        self.run_tool('track', '--action', 'apply-files', '--chezmoi', self.chezmoi,
                      '--make', self.make, expected=expected)
        sessions = list(self.sessions.glob('*.json'))
        self.assertEqual(len(sessions), 1)
        self.assertEqual(stat.S_IMODE(sessions[0].stat().st_mode), 0o600)
        return sessions[0].stem

    def test_preview_then_restore_files_links_and_modes(self):
        session = self.track()
        preview = self.run_tool('plan', '--run', session)
        self.assertIn('.config/with space', preview)
        self.assertEqual(self.zshrc.read_text(), 'applied')
        self.assertTrue((self.home / '.config/link').is_symlink())

        self.run_tool('restore', '--run', session)
        self.assertEqual(self.zshrc.read_text(), 'personal')
        self.assertEqual(stat.S_IMODE(self.zshrc.stat().st_mode), 0o600)
        self.assertFalse((self.home / '.config').exists())
        self.assertIn('復元済み', self.run_tool('restore', '--run', session))

    def test_failure_is_recoverable_without_overwriting_later_edits(self):
        self.env['FAKE_MAKE_STATUS'] = '7'
        session = self.track(expected=7)
        self.zshrc.write_text('edited after setup')
        self.assertIn('競合', self.run_tool('plan', '--run', session, expected=1))
        self.run_tool('restore', '--run', session, '--target', '.config/link')
        self.assertTrue((self.home / '.config/with space').exists())
        unmanaged = self.home / '.config/personal'
        unmanaged.write_text('keep')
        self.run_tool('restore', '--run', session, expected=1)
        self.assertEqual(self.zshrc.read_text(), 'edited after setup')
        self.assertEqual(unmanaged.read_text(), 'keep')

    def test_symlinked_parent_stops_before_setup(self):
        external = self.root / 'external'
        external.mkdir()
        (self.home / '.config').symlink_to(external)
        self.run_tool('track', '--action', 'apply-files', '--chezmoi', self.chezmoi,
                      '--make', self.make, expected=1)
        self.assertEqual(self.zshrc.read_text(), 'personal')
        self.assertEqual(list(external.iterdir()), [])
        self.assertEqual(list(self.sessions.glob('*.json')), [])

    def test_legacy_preview_does_not_create_state(self):
        (self.home / '.zshrc.backup').write_text('old')
        self.assertIn('.zshrc.backup', self.run_tool('legacy', '--chezmoi', self.chezmoi))
        self.assertFalse(self.sessions.exists())
        self.assertEqual(self.zshrc.read_text(), 'personal')


if __name__ == '__main__':
    unittest.main()
