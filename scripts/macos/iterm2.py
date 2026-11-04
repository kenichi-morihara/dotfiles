#!/usr/bin/env python3
"""Merge declared iTerm2 profile settings without replacing unrelated preferences."""
import argparse
import copy
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import uuid

DOMAIN = 'com.googlecode.iterm2'


def merge_preferences(current, config):
    result = copy.deepcopy(current)
    profiles = result.setdefault('New Bookmarks', [])
    default_guid = result.get('Default Bookmark Guid')
    base = next((p for p in profiles if p.get('Guid') == default_guid),
                profiles[0] if profiles else {'Custom Command': 'No', 'Custom Directory': 'No'})
    # New profiles inherit the existing default's colors and shell settings.
    base = copy.deepcopy(base)
    managed = {}
    for declared in config['profiles']:
        # Dynamic profiles are owned by their JSON file; they may share a name
        # with a saved profile and must not make that saved profile ambiguous.
        matches = [p for p in profiles if p.get('Name') == declared['Name']
                   and not p.get('Is Dynamic Profile') and not p.get('Dynamic Profile Filename')]
        if len(matches) > 1:
            raise ValueError(f'Duplicate iTerm2 profile name: {declared["Name"]}')
        if matches:
            profile = matches[0]
        else:
            profile = copy.deepcopy(base)
            # A normal profile must not inherit the default profile's hotkey.
            for key in list(profile):
                if key.startswith('HotKey ') or key in (
                        'Has Hotkey', 'Keyboard Map', 'Is Dynamic Profile',
                        'Dynamic Profile Filename', 'Dynamic Profile Parent Name'):
                    del profile[key]
            profile['Guid'] = str(uuid.uuid5(uuid.NAMESPACE_URL,
                                           'dotfiles:iterm2:' + declared['Name'])).upper()
            profiles.append(profile)
        profile.update(declared)
        managed[declared['Name']] = profile
    default = managed[config['defaultProfile']]
    result['Default Bookmark Guid'] = default['Guid']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sys.platform != 'darwin':
        raise SystemExit('iTerm2 settings are supported on macOS only')
    exported = subprocess.run(['defaults', 'export', DOMAIN, '-'], capture_output=True)
    current = plistlib.loads(exported.stdout) if exported.returncode == 0 else {}
    if current.get('LoadPrefsFromCustomFolder'):
        raise SystemExit('iTerm2 uses an external preferences folder; disable it before applying')
    config = json.loads(Path(__file__).with_name('iterm2.json').read_text())
    desired = merge_preferences(current, config)
    if args.check:
        print("iTerm2 settings match" if desired == current else "iTerm2 settings differ")
        return int(desired != current)
    if desired == current:
        print('iTerm2 settings already match')
        return
    if subprocess.run(['pgrep', '-x', 'iTerm2'], capture_output=True).returncode == 0:
        raise SystemExit('Quit iTerm2, then run make apply-apps from Terminal.app. '
                         'No iTerm2 settings were changed.')
    directory = Path.home() / 'Library/Application Support/iTerm2/dotfiles-backups'
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=directory, prefix='preferences.', suffix='.plist') as updated:
        plistlib.dump(desired, updated)
        updated.flush()
        if current:
            with tempfile.NamedTemporaryFile(dir=directory, prefix='backup.', suffix='.plist',
                                             delete=False) as backup:
                plistlib.dump(current, backup)
                print(f'Backup: {backup.name}')
        subprocess.run(['defaults', 'import', DOMAIN, updated.name], check=True)
    print('iTerm2 settings applied. Open iTerm2 to use them.')


if __name__ == '__main__':
    sys.exit(main())
