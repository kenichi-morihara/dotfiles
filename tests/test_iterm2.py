"""Check profile changes preserve machine-local terminal settings."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('iterm2_settings', ROOT / 'scripts/macos/iterm2.py')
iterm2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iterm2)


class ITerm2Tests(unittest.TestCase):
    def test_existing_profiles_keep_guids_colors_commands_and_other_profiles(self):
        current = {'Other': 'keep', 'Default Bookmark Guid': 'original', 'New Bookmarks': [
            {'Name': 'Dracula', 'Guid': 'original', 'Command': '/local/shell', 'Colors': 'keep'},
            {'Name': 'Hotkey Window', 'Guid': 'hotkey', 'Keyboard Map': {'local': 'keep'}},
            {'Name': 'Work', 'Guid': 'work'},
        ]}
        config = json.loads((ROOT / 'scripts/macos/iterm2.json').read_text())
        updated = iterm2.merge_preferences(current, config)
        self.assertEqual(updated['Other'], 'keep')
        self.assertEqual(updated['New Bookmarks'][0]['Guid'], 'original')
        self.assertEqual(updated['New Bookmarks'][0]['Command'], '/local/shell')
        self.assertEqual(updated['New Bookmarks'][0]['Colors'], 'keep')
        self.assertEqual(updated['New Bookmarks'][1]['Keyboard Map'], {'local': 'keep'})
        self.assertEqual(updated['New Bookmarks'][2], current['New Bookmarks'][2])
        self.assertEqual(updated['New Bookmarks'][1]['HotKey Modifier Activation'], 0)
        self.assertTrue(updated['New Bookmarks'][1]['HotKey Activated By Modifier'])
        self.assertEqual(iterm2.merge_preferences(updated, config), updated)
        self.assertNotIn('Normal Font', current['New Bookmarks'][0])

    def test_new_machine_creates_distinct_stable_profiles(self):
        config = json.loads((ROOT / 'scripts/macos/iterm2.json').read_text())
        updated = iterm2.merge_preferences({}, config)
        profiles = updated['New Bookmarks']
        self.assertEqual(len({p['Guid'] for p in profiles}), 2)
        self.assertEqual(updated['Default Bookmark Guid'], profiles[0]['Guid'])
        self.assertEqual(iterm2.merge_preferences({}, config), updated)

    def test_new_hotkey_profile_does_not_inherit_dynamic_profile_ownership(self):
        current = {'Default Bookmark Guid': 'dynamic', 'New Bookmarks': [
            {'Name': 'Dracula', 'Guid': 'dynamic', 'Is Dynamic Profile': True,
             'Dynamic Profile Filename': '/local/DynamicProfiles/dotfiles.json',
             'Dynamic Profile Parent Name': 'Default', 'Command': '/local/shell'},
        ]}
        config = json.loads((ROOT / 'scripts/macos/iterm2.json').read_text())
        updated = iterm2.merge_preferences(current, config)
        hotkey = next(p for p in updated['New Bookmarks'] if p['Name'] == 'Hotkey Window')
        self.assertNotIn('Is Dynamic Profile', hotkey)
        self.assertNotIn('Dynamic Profile Filename', hotkey)
        self.assertNotIn('Dynamic Profile Parent Name', hotkey)
        self.assertEqual(hotkey['Command'], '/local/shell')
        self.assertTrue(updated['New Bookmarks'][0]['Is Dynamic Profile'])
        self.assertEqual(iterm2.merge_preferences(updated, config), updated)
