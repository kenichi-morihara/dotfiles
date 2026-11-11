"""Ensure every module can render after being copied out of the monorepo."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ModuleIsolationTests(unittest.TestCase):
    def test_every_module_runs_from_an_unrelated_directory(self):
        for name in json.loads((ROOT / "modules/registry.json").read_text()):
            with self.subTest(module=name), tempfile.TemporaryDirectory() as directory:
                module = Path(directory) / "standalone"
                shutil.copytree(ROOT / "modules" / name, module,
                                ignore=shutil.ignore_patterns("__pycache__", ".venv", ".validation", ".git"))
                for file in ["Makefile", "README.md", ".chezmoiroot", "module.json", "LICENSE", "THIRD_PARTY.md"]:
                    self.assertTrue((module / file).is_file(), (name, file))
                result = subprocess.run(["make", "--no-print-directory", "test", "PYTHON=" + sys.executable], cwd=module,
                                        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, name + "\n" + result.stdout + result.stderr)
