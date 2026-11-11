"""Install the opt-in, work-only Claude admin configuration."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import venv
from contextlib import contextmanager
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


def enable_default(root, settings):
    target = Path.home() / ".claude/settings.json"
    with settings_lock(target):
        merge_default(root, settings, target)


def merge_default(root, settings, target):
    current = json.loads(target.read_text()) if target.exists() else {}
    before = json.dumps(current, sort_keys=True)
    allow = current.setdefault("permissions", {}).setdefault("allow", [])
    for rule in settings["permissions"]["allow"]:
        if rule not in allow:
            allow.append(rule)
    hooks = current.setdefault("hooks", {}).setdefault("PreToolUse", [])
    for hook in settings["hooks"]["PreToolUse"]:
        if hook not in hooks:
            hooks.append(hook)
    if json.dumps(current, sort_keys=True) == before:
        return
    if target.exists():
        with tempfile.NamedTemporaryFile(prefix="user-settings-backup.", suffix=".json",
                                         dir=root, delete=False) as backup:
            saved = Path(backup.name)
            backup.write(target.read_bytes())
        print(f"個人設定のバックアップ: {saved}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", prefix=".settings.", dir=target.parent, delete=False) as temp:
        temp.write(json.dumps(current, indent=2, ensure_ascii=False) + "\n")
        temp_path = Path(temp.name)
    try:
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)


def install(default=False):
    source = Path(__file__).resolve().parent
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dotfiles"
    profile = config / "profile"
    standalone = os.environ.get("STANDALONE") == "1"
    if not standalone and (not profile.exists() or not (
        profile.read_text().strip() == "work" or profile.read_text().strip().startswith("work/")
    )):
        raise RuntimeError("会社用 profile を選んでから make claude-admin-setup を実行してください。")

    tools = {name: shutil.which(name) for name in ("claude", "git", "docker")}
    if not all(tools.values()):
        raise RuntimeError("claude・git・docker を PATH に用意してください。")
    root = config / "claude-admin"
    launcher = Path.home() / ".local/bin/claude-admin"
    if launcher.exists() and "# dotfiles Claude admin launcher" not in launcher.read_text():
        raise RuntimeError(f"既存のランチャーを確認してください: {launcher}")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = root / ".install-lock"
    lock.mkdir(mode=0o700)
    try:
        environment = root / ".venv"
        if not (environment / "bin/python").exists():
            venv.create(environment, with_pip=True)
        subprocess.run([
            str(environment / "bin/python"), "-m", "pip", "install", "--disable-pip-version-check",
            "--require-hashes", "--only-binary=:all:", "-r", str(source / "requirements.txt"),
        ], check=True)

        def write(name, contents, mode=0o600):
            target = root / name
            temp = target.with_name(target.name + ".tmp")
            temp.write_text(contents)
            temp.chmod(mode)
            temp.replace(target)

        (root / "bin").mkdir(exist_ok=True, mode=0o700)
        if standalone:
            write(".standalone", "enabled\n")
        write("rewrite.py", (source / "rewrite.py").read_text())
        write("tools.json", json.dumps(tools, indent=2) + "\n")
        for name in ("admin-git", "admin-compose"):
            # An absolute interpreter also works in Claude's non-interactive shell.
            write("bin/" + name, f"#!{sys.executable}\n" + (source / "admin-tool.py").read_text(), 0o700)
        hook_command = shlex.join([str(environment / "bin/python"), str(root / "rewrite.py")])
        settings = {
            "permissions": {"allow": [
                f"Bash({root / 'bin/admin-git'} *)",
                f"Bash({root / 'bin/admin-compose'} *)",
            ]},
            "hooks": {"PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": hook_command, "timeout": 10}],
            }]},
        }
        write("settings.json", json.dumps(settings, indent=2) + "\n")
        write("prompt.txt", (
            "This is the explicitly enabled company administrator configuration. "
            f"For Git, use {shlex.quote(str(root / 'bin/admin-git'))} with normal git arguments. "
            f"For Docker Compose, use {shlex.quote(str(root / 'bin/admin-compose'))} "
            "with the arguments that normally follow docker compose. "
            "The PreToolUse hook redirects ordinary Git and Docker Compose commands to these tools. "
            "If a shell command cannot be parsed, split it into simpler Bash calls.\n"
        ))
        launcher.parent.mkdir(parents=True, exist_ok=True)
        temp_launcher = launcher.with_name(launcher.name + ".tmp")
        temp_launcher.write_text((source / "launch.sh").read_text())
        temp_launcher.chmod(0o700)
        temp_launcher.replace(launcher)
        if default:
            enable_default(root, settings)
    finally:
        lock.rmdir()
    command = "claude" if default else "claude-admin"
    print(f"完了。会社用 profile で {command} を起動してください。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--default", action="store_true", help="この端末の通常の claude にも仕事用フックを登録")
    args = parser.parse_args()
    try:
        install(default=args.default)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
