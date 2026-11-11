"""Apply module-owned files twice in an isolated HOME without native app changes."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("chezmoi"), "chezmoi is required")
class DistributionTests(unittest.TestCase):
    def test_file_apply_is_repeatable_and_preserves_unmanaged_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            (home / "keep.txt").write_text("unmanaged")
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(base / "config"),
                       XDG_DATA_HOME=str(base / "data"), XDG_CACHE_HOME=str(base / "cache"))
            command = ["chezmoi", "--source", str(ROOT), "--destination", str(home),
                       "--config", str(base / "config/chezmoi.toml"),
                       "--persistent-state", str(base / "state/chezmoi.boltdb")]
            # App launch, credentials and machine-wide mutations are tested with stubs.
            command += ["--exclude", "scripts"]
            subprocess.run(command + ["apply"], env=env, check=True, capture_output=True)
            before = {str(p.relative_to(home)): p.read_bytes() for p in home.rglob("*") if p.is_file()}
            subprocess.run(command + ["apply"], env=env, check=True, capture_output=True)
            after = {str(p.relative_to(home)): p.read_bytes() for p in home.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual((home / "keep.txt").read_text(), "unmanaged")
            subprocess.run(command + ["verify"], env=env, check=True, capture_output=True)
