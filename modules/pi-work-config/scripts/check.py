"""Check the installed isolated Pi runtime without making a model request."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dotfiles/pi"
files = ["agent/settings.json", "claude-bridge",
         "runtime-1.5.1-1.2.1/node_modules/claude-code-pi/src/index.ts"]
if not all((root / name).is_file() for name in files):
    sys.exit("Run make apply to install Pi")
sys.exit(subprocess.run([str(root / "runtime-1.5.1-1.2.1/node_modules/.bin/pi"), "--version"]).returncode)
