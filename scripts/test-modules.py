#!/usr/bin/env python3
"""Run root integration tests and each module's local tests."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
for directory in [root, *(root / "modules" / name for name in json.loads((root / "modules/registry.json").read_text()))]:
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=directory)
    if result.returncode:
        sys.exit(result.returncode)
