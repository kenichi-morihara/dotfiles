"""Work-only pi setup: guards run against a disposable home, never installing anything."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PI = ROOT / 'work/pi'
EXTENSION = PI / 'agent/extensions/claude-permissions'


class PiSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        # npm/mise stubs record any call so tests can prove the guards stop first.
        bin_dir = self.home / 'bin'
        bin_dir.mkdir()
        for name in ('npm', 'mise'):
            stub = bin_dir / name
            stub.write_text(f'#!/bin/sh\necho {name} "$@" >> "{self.home}/calls"\n')
            stub.chmod(0o755)
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / '.config'),
                        PATH=f'{bin_dir}:{os.environ["PATH"]}')

    def install(self, profile=None):
        if profile:
            target = self.home / '.config/dotfiles/profile'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(profile + '\n')
        return subprocess.run(['bash', str(PI / 'install.sh')], env=self.env,
                              capture_output=True, text=True)

    def assert_nothing_installed(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / 'calls').exists())
        self.assertFalse((self.home / '.pi').exists())

    def test_settings_are_valid_json(self):
        settings = json.loads((PI / 'agent/settings.json').read_text())
        self.assertEqual(settings['defaultProjectTrust'], 'ask')

    def test_stops_without_work_profile(self):
        self.assert_nothing_installed(self.install())
        self.assert_nothing_installed(self.install('personal'))

    def test_installs_for_work_profile(self):
        agent = self.home / '.pi/agent'
        (agent).mkdir(parents=True)
        (agent / 'settings.json').write_text('{"old": true}\n')
        (agent / 'auth.json').write_text('{"token": "keep"}\n')
        result = self.install('work/laptop')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('npm install -g --ignore-scripts @earendil-works/pi-coding-agent',
                      (self.home / 'calls').read_text())
        self.assertEqual((agent / 'settings.json').read_text(), (PI / 'agent/settings.json').read_text())
        self.assertEqual((agent / 'settings.json.backup').read_text(), '{"old": true}\n')
        self.assertEqual((agent / 'auth.json').read_text(), '{"token": "keep"}\n')
        self.assertTrue((agent / 'extensions/claude-permissions/index.ts').exists())
        self.assertFalse((agent / 'extensions/claude-permissions/rules.test.ts').exists())

    def test_extension_has_no_bypass(self):
        source = (EXTENSION / 'index.ts').read_text() + (EXTENSION / 'rules.ts').read_text()
        source = re.sub(r'//.*', '', source)  # Comments may mention what is deliberately absent.
        self.assertIsNone(re.search(r'yolo|bypass|process\.env|registerFlag|registerCommand', source, re.I))

    def test_not_distributed_by_chezmoi(self):
        self.assertEqual((ROOT / '.chezmoiroot').read_text().strip(), 'home')

    def test_rules(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('node not installed')
        version = subprocess.check_output([node, '-p', 'process.versions.node'], text=True).strip()
        major, minor = map(int, version.split('.')[:2])
        if (major, minor) < (22, 18):
            self.skipTest('node without TypeScript stripping')
        result = subprocess.run([node, '--test', str(EXTENSION / 'rules.test.ts')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
