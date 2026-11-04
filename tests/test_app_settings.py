"""Exercise skipping, failure isolation and no-op preference application."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AppSettingsTests(unittest.TestCase):
    def test_missing_nani_is_skipped_and_failure_does_not_stop_later_apps(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            apps = root / 'apps'
            apps.mkdir()
            for app in ['Rectangle', 'iTerm']:
                (apps / (app + '.app')).mkdir()
            scripts = root / 'scripts'
            scripts.mkdir()
            shutil.copy(ROOT / 'scripts/macos/apps.sh', scripts / 'apps.sh')
            (scripts / 'rectangle.sh').write_text('echo rectangle-failed\nexit 7\n')
            (scripts / 'iterm2.py').write_text('print("iterm-ran")\n')
            (scripts / 'nani.py').write_text('raise Exception("must skip")\n')
            binaries = root / 'bin'
            binaries.mkdir()
            uname = binaries / 'uname'
            uname.write_text('#!/bin/sh\necho Darwin\n')
            uname.chmod(0o755)
            swift = binaries / 'swift'
            swift.write_text('#!/bin/sh\necho input-sources-ran\n')
            swift.chmod(0o755)
            env = {**os.environ, 'HOME': str(root), 'DOTFILES_APPLICATIONS_DIR': str(apps),
                   'PATH': str(binaries) + ':' + os.environ['PATH']}
            result = subprocess.run(['bash', str(scripts / 'apps.sh')], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('SKIP Nani: not installed', result.stdout)
            self.assertIn('iterm-ran', result.stdout)
            self.assertIn('Failed: Rectangle', result.stderr)

    def test_rectangle_matching_settings_never_write_backup_or_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            binaries = root / 'bin'
            binaries.mkdir()
            # Defaults supports only read-only export here: writes would fail the test.
            defaults = binaries / 'defaults'
            defaults.write_text('''#!/usr/bin/env python3
import plistlib, sys
assert sys.argv[1:] == ['export', 'com.knollsoft.Rectangle', '-']
keys = [('leftHalf',123,1835008), ('rightHalf',124,1835008), ('maximize',126,1835008),
        ('restore',125,1835008), ('previousDisplay',123,1966080), ('nextDisplay',124,1966080)]
sys.stdout.buffer.write(plistlib.dumps({a:dict(keyCode=k,modifierFlags=f) for a,k,f in keys}))
''')
            defaults.chmod(0o755)
            uname = binaries / 'uname'
            uname.write_text('#!/bin/sh\necho Darwin\n')
            uname.chmod(0o755)
            env = {**os.environ, 'HOME': str(root), 'PATH': str(binaries) + ':' + os.environ['PATH']}
            for mode in [[], [], ['--check']]:
                result = subprocess.run(['bash', str(ROOT / 'scripts/macos/rectangle.sh'), *mode],
                                        env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('already match', result.stdout)
            self.assertFalse((root / 'Library').exists())
