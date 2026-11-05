#!/usr/bin/env python3
"""Apply explicitly selected Nani preferences without distributing its database."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time

ALLOWED = {
    'user-custom-shortcuts': {'translate-select', 'translate-new'},
    'local-settings': {'theme', 'translateLang', 'translateBcp47', 'allowParaphrase',
                       'rubyType', 'preferredModelType', 'submitKey', 'inAppHotkeys'},
}


class NotInitialized(ValueError):
    """Nani has not created the preferences managed by dotfiles yet."""


def load_config(path):
    config = json.loads(path.read_text())
    for key, values in config.items():
        if key not in ALLOWED or not isinstance(values, dict) or set(values) - ALLOWED[key]:
            raise ValueError(f'Unsupported Nani setting: {key}')
    return config


def updates(connection, config):
    result = {}
    for key, values in config.items():
        row = connection.execute('SELECT value FROM localkv WHERE key = ?', (key,)).fetchone()
        if row is None:
            raise NotInitialized(f'Nani setting {key} is missing; configure Nani once first.')
        current = json.loads(row[0])
        if not isinstance(current, dict):
            raise ValueError(f'Unexpected Nani setting format: {key}')
        merged = {**current, **values}
        if merged != current:
            result[key] = (row[0], json.dumps(merged, ensure_ascii=False))
    return result


def apply_settings(database, config, backup_dir):
    # mode=rw prevents accidentally creating an empty database on a new machine.
    with sqlite3.connect(database.as_uri() + '?mode=rw', uri=True) as connection:
        connection.execute('BEGIN IMMEDIATE')
        changes = updates(connection, config)
        if not changes:
            return False
        backup_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', prefix='preferences.', suffix='.json',
                                         dir=backup_dir, delete=False) as backup:
            json.dump({key: json.loads(old) for key, (old, _) in changes.items()},
                      backup, ensure_ascii=False, indent=2)
            print(f'Backup: {backup.name}')
        for key, (_, value) in changes.items():
            connection.execute('UPDATE localkv SET value = ? WHERE key = ?', (value, key))
    return True


def is_running():
    return subprocess.run(['pgrep', '-x', 'Nani'], capture_output=True).returncode == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check settings without writing')
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('Nani preferences are supported on macOS only')
    directory = Path.home() / 'Library/Application Support/Nani'
    database = directory / 'app.db/db'
    if not database.is_file():
        print('SKIP Nani: launch it and configure selected-text translation once first')
        return 0
    config = load_config(Path(__file__).with_name('nani.json'))
    try:
        with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
            changed = bool(updates(connection, config))
    except NotInitialized as error:
        print(f'SKIP Nani: {error}')
        return 0
    if args.check:
        print('Nani settings differ' if changed else 'Nani settings match')
        return int(changed)
    if not changed:
        print('Nani settings already match')
        return 0
    running = is_running()
    if running:
        subprocess.run(['osascript', '-e', 'tell application "Nani" to quit'], check=True)
        for _ in range(50):
            if not is_running():
                break
            time.sleep(0.1)
        if is_running():
            raise RuntimeError('Nani did not quit; settings were not changed')
    try:
        apply_settings(database, config, directory / 'dotfiles-backups')
    finally:
        if running:
            subprocess.run(['open', '-a', 'Nani'], check=True)
    print('Nani settings applied')
    return 0


if __name__ == '__main__':
    sys.exit(main())
