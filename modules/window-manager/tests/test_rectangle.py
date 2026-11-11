import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RectangleTests(unittest.TestCase):
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
