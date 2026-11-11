"""Run Git or Docker Compose without interpreting their arguments as shell code."""
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
profile_file = root.parent / "profile"
profile = profile_file.read_text().strip() if profile_file.exists() else ""
if not (root / ".standalone").exists() and profile != "work" and not profile.startswith("work/"):
    sys.exit("管理者用コマンドは会社用 profile 専用です。")
tools = json.loads((root / "tools.json").read_text())
name = Path(sys.argv[0]).name
if name == "admin-git":
    args = [tools["git"], *sys.argv[1:]]
elif name == "admin-compose":
    args = [tools["docker"], "compose", *sys.argv[1:]]
else:
    sys.exit("管理者用コマンド名を確認してください。")
os.execv(args[0], args)
