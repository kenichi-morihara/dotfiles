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

    def test_us_command_taps_preserve_command_chords(self):
        config = self.render('us')
        selected = [p for p in config['profiles'] if p.get('selected')]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['virtual_hid_keyboard']['keyboard_type_v2'], 'ansi')
        manipulators = {m['from']['key_code']: m
                        for r in selected[0]['complex_modifications']['rules']
                        for m in r['manipulators']}
        for side, output in [('left', 'japanese_eisuu'), ('right', 'japanese_kana')]:
            key = side + '_command'
            self.assertEqual(manipulators[key]['to'], [{'key_code': key}])
            self.assertEqual(manipulators[key]['to_if_alone'], [{'key_code': output}])

    def test_caps_lock_and_control_pass_through_in_all_profiles(self):
        # macOS swaps these modifiers on the virtual keyboard. A Caps Lock
        # hold/tap rule would turn Control+C into extra modifiers on this Mac.
        for layout in ('jis', 'us'):
            config = self.render(layout)
            for profile in config['profiles']:
                for rule in profile['complex_modifications']['rules']:
                    for manipulator in rule['manipulators']:
                        self.assertNotIn(manipulator['from'].get('key_code'),
                                         ('caps_lock', 'left_control', 'right_control'))



if __name__ == '__main__':
    unittest.main()
