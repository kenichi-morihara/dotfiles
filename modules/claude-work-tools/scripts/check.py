"""Verify the installed work-tool files and their default registration."""
import json
import os
from pathlib import Path
import sys

root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dotfiles/claude-admin"
required = ["settings.json", "tools.json", "rewrite.py", "bin/admin-git", "bin/admin-compose", ".venv/bin/python"]
missing = [name for name in required if not (root / name).is_file()]
if missing:
    sys.exit("Missing installed files: " + ", ".join(missing))
desired = json.loads((root / "settings.json").read_text())
target = Path.home() / ".claude/settings.json"
current = json.loads(target.read_text()) if target.exists() else {}
ok = all(rule in current.get("permissions", {}).get("allow", []) for rule in desired["permissions"]["allow"])
ok = ok and all(hook in current.get("hooks", {}).get("PreToolUse", []) for hook in desired["hooks"]["PreToolUse"])
sys.exit(0 if ok else "Claude work tools are not registered in the default settings")
