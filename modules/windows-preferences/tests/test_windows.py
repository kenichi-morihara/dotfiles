"""Validate PowerShell syntax and read-only checks on Windows."""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "win32" and shutil.which("pwsh"), "PowerShell tests run on Windows CI")
class WindowsTests(unittest.TestCase):
    def test_check_uses_read_only_resource_queries(self):
        subprocess.run(["pwsh", "-NoProfile", "-File", str(ROOT / "tests/read-only.ps1")], check=True)
