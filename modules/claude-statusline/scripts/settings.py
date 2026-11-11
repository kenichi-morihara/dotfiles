"""Merge only status-line preferences under the same lock as Claude work tools."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
import time


@contextmanager
def settings_lock(target):
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = target.parent / ".dotfiles-settings.lock"
    deadline = time.monotonic() + 10
    while True:
        try:
            lock.mkdir(mode=0o700)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeError("Claude settings are being updated by another process")
            time.sleep(0.05)
    try:
        yield
    finally:
        lock.rmdir()


def update(check=False):
    root = Path(__file__).resolve().parents[1]
    fragment = json.loads((root / "settings-fragment.json").read_text())
    target = Path.home() / ".claude/settings.json"
    if check:
        current = json.loads(target.read_text()) if target.exists() else {}
        return int(any(current.get(key) != value for key, value in fragment.items()))
    with settings_lock(target):
        current = json.loads(target.read_text()) if target.exists() else {}
        desired = {**current, **fragment}
        if current == desired:
            return 0
        if target.exists():
            backup_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "claude-statusline/backups"
            backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            with tempfile.NamedTemporaryFile(prefix="settings.", suffix=".json", dir=backup_dir, delete=False) as backup:
                backup.write(target.read_bytes())
        with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, delete=False) as temp:
            temp.write(json.dumps(desired, indent=2, ensure_ascii=False) + "\n")
            temporary = Path(temp.name)
        try:
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(update(check="--check" in sys.argv))
