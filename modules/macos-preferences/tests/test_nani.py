"""Verify preference merging never replaces translation or account data."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('nani_settings', ROOT / 'scripts/macos/nani.py')
nani = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nani)


class NaniTests(unittest.TestCase):
    def test_check_reports_changed_fields_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / 'Library/Application Support/Nani/app.db/db'
            database.parent.mkdir(parents=True)
            with sqlite3.connect(database) as connection:
                connection.execute('CREATE TABLE localkv (key TEXT PRIMARY KEY, value TEXT)')
                connection.executemany('INSERT INTO localkv VALUES (?, ?)', [
                    ('local-settings', '{"theme":"dark","private":"do not print"}'),
                    ('user-custom-shortcuts', '{}'),
                ])
            before = database.read_bytes()
            output = io.StringIO()
            with patch.object(nani.sys, 'argv', ['nani.py', '--check']), \
                 patch.object(nani.sys, 'platform', 'darwin'), \
                 patch.object(nani.Path, 'home', return_value=root), \
                 contextlib.redirect_stdout(output):
                self.assertEqual(nani.main(), 1)
            self.assertIn('local-settings.theme: "dark" ->', output.getvalue())
            self.assertIn('make apply-apps', output.getvalue())
            self.assertNotIn('do not print', output.getvalue())
            self.assertEqual(database.read_bytes(), before)

    def test_apply_preserves_history_account_and_unmanaged_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / 'db'
            with sqlite3.connect(database) as connection:
                connection.execute('CREATE TABLE localkv (key TEXT PRIMARY KEY, value TEXT)')
                connection.execute('CREATE TABLE basic_translate (source_text TEXT)')
                connection.execute("INSERT INTO basic_translate VALUES ('private history')")
                connection.executemany('INSERT INTO localkv VALUES (?, ?)', [
                    ('act', 'private account'),
                    ('local-settings', json.dumps({'theme': 'dark', 'onboardedAt': 123})),
                    ('user-custom-shortcuts', json.dumps({'open-app': ['Meta', 'KeyN']})),
                ])
            config = nani.load_config(ROOT / 'scripts/macos/nani.json')
            self.assertTrue(nani.apply_settings(database, config, root / 'backups'))
            with sqlite3.connect(database) as connection:
                rows = dict(connection.execute('SELECT key, value FROM localkv'))
                self.assertEqual(rows['act'], 'private account')
                self.assertEqual(json.loads(rows['local-settings'])['onboardedAt'], 123)
                self.assertEqual(json.loads(rows['user-custom-shortcuts'])['open-app'], ['Meta', 'KeyN'])
                self.assertEqual(connection.execute('SELECT source_text FROM basic_translate').fetchone()[0],
                                 'private history')
            self.assertFalse(nani.apply_settings(database, config, root / 'backups'))
            self.assertEqual(len(list((root / 'backups').iterdir())), 1)

    def test_missing_preference_rolls_back_without_partial_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / 'db'
            with sqlite3.connect(database) as connection:
                connection.execute('CREATE TABLE localkv (key TEXT PRIMARY KEY, value TEXT)')
                connection.execute("INSERT INTO localkv VALUES ('local-settings', '{}')")
            with self.assertRaises(ValueError):
                nani.apply_settings(database, nani.load_config(ROOT / 'scripts/macos/nani.json'), root / 'backups')
            self.assertFalse((root / 'backups').exists())
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute('SELECT value FROM localkv').fetchone()[0], '{}')
