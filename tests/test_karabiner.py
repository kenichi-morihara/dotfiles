"""Render per-machine keyboard profiles without changing the host keyboard."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KarabinerTests(unittest.TestCase):
    def render(self, layout):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                       XDG_DATA_HOME=str(home / '.local/share'),
                       XDG_CACHE_HOME=str(home / '.cache'))
            local_config = home / '.config/chezmoi/chezmoi.toml'
            local_config.parent.mkdir(parents=True)
            local_config.write_text('[data]\nkeyboardLayout = ' + json.dumps(layout) + '\n')
            command = ['chezmoi', '--source', str(ROOT), '--destination', str(home),
                       '--override-data', json.dumps({'chezmoi': {'os': 'darwin'}})]
            subprocess.run(command + ['init', '--apply'], env=env, check=True,
                           capture_output=True)
            config = json.loads((home / '.config/karabiner/karabiner.json').read_text())
            # init must persist the choice for later applies without override-data.
            later = subprocess.run(command[:5] + ['data', '--format', 'json'],
                                   env=env, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(later.stdout)['keyboardLayout'], layout)
            return config

    def test_jis_keeps_dedicated_language_keys(self):
        config = self.render('jis')
        selected = [p for p in config['profiles'] if p.get('selected')]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['virtual_hid_keyboard']['keyboard_type_v2'], 'jis')
        manipulators = [m for r in selected[0]['complex_modifications']['rules']
                        for m in r['manipulators']]
        self.assertEqual([m['from']['key_code'] for m in manipulators], ['v'])

    def test_raycast_binding_is_available_in_both_layouts(self):
        for layout in ('jis', 'us'):
            config = self.render(layout)
            for profile in config['profiles']:
                rules = profile['complex_modifications']['rules']
                binding = next(r for r in rules if r['description'].startswith('Raycast:'))
                manipulator, = binding['manipulators']
                self.assertEqual(manipulator['from'], {
                    'key_code': 'v',
                    'modifiers': {'mandatory': ['command', 'shift']},
                })
                self.assertEqual(manipulator['to'], [{'shell_command':
                    "/usr/bin/open -g 'raycast://extensions/raycast/clipboard-history/clipboard-history'"}])

    def test_us_modifiers_and_command_taps(self):
        config = self.render('us')
        selected = [p for p in config['profiles'] if p.get('selected')]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['virtual_hid_keyboard']['keyboard_type_v2'], 'ansi')
        manipulators = [m for r in selected[0]['complex_modifications']['rules']
                        for m in r['manipulators']]
        remaps = {m['from']['key_code']: m['to'] for m in manipulators
                  if m['from']['key_code'] in ('fn', 'left_control', 'left_option')}
        self.assertEqual(remaps, {
            'fn': [{'key_code': 'left_control'}],
            'left_control': [{'key_code': 'left_option'}],
            'left_option': [{'key_code': 'left_command'}],
        })
        left, = (m for m in manipulators if m['from']['key_code'] == 'left_command')
        self.assertEqual(left['to'], [{'key_code': 'left_command'}])
        self.assertEqual(left['to_if_alone'], [{'key_code': 'japanese_eisuu'}])
        self.assertNotIn('conditions', left)

        right, = (m for m in manipulators if m['from']['key_code'] == 'right_command')
        self.assertEqual(right['to'], [{'key_code': 'right_command'}])
        self.assertEqual(right['to_if_alone'], [{'key_code': 'japanese_kana'}])
        self.assertEqual(sum('to_if_alone' in m for m in manipulators), 2)

    def test_caps_lock_and_right_control_pass_through(self):
        for layout in ('jis', 'us'):
            config = self.render(layout)
            for profile in config['profiles']:
                untouched = {'caps_lock', 'right_control'}
                if profile['name'] != 'QWERTY US':
                    untouched.add('left_control')
                for rule in profile['complex_modifications']['rules']:
                    for manipulator in rule['manipulators']:
                        self.assertNotIn(manipulator['from'].get('key_code'), untouched)



if __name__ == '__main__':
    unittest.main()
