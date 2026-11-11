"""Rewrite executable words in Bash syntax while preserving all other source text."""
import json
from pathlib import Path
import re
import shlex
import sys

import bashlex


def rewrite(command, root):
    changes = []
    only_admin_commands = True

    class Commands(bashlex.ast.nodevisitor):
        def visitcommand(self, node, parts):
            nonlocal only_admin_commands
            words = [part for part in parts if part.kind == "word"]
            if not words:
                only_admin_commands = False
                return
            executable = words[0]
            name = Path(executable.word).name
            alias = None
            if not executable.parts and name == "git":
                alias = "admin-git"
            elif not executable.parts and name == "docker-compose":
                alias = "admin-compose"
            elif (not executable.parts and name == "docker" and len(words) > 1
                  and words[1].word == "compose" and not words[1].parts):
                alias = "admin-compose"
                changes.append((*words[1].pos, ""))
            elif executable.word in (str(root / "bin/admin-git"), str(root / "bin/admin-compose")):
                return
            if alias:
                changes.append((*executable.pos, shlex.quote(str(root / "bin" / alias))))
            else:
                only_admin_commands = False

    visitor = Commands()
    for node in bashlex.parse(command):
        visitor.visit(node)
    for start, end, replacement in sorted(changes, reverse=True):
        command = command[:start] + replacement + command[end:]
    return command, bool(changes), only_admin_commands


def handle(event, root):
    if event.get("tool_name") != "Bash":
        return {}
    tool_input = event["tool_input"]
    command = tool_input["command"]
    try:
        updated, changed, only_admin = rewrite(command, root)
    except (bashlex.errors.ParsingError, NotImplementedError, ValueError):
        # Ask the model to simplify target calls, without approving an opaque script.
        if re.search(r"\b(?:git|docker|docker-compose)\b", command):
            return {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "管理者用コマンドへ変換できません。Git / Docker Compose を単純な Bash 呼び出しに分けて再試行してください。",
            }}
        return {}
    if not changed:
        return {}
    output = {
        "hookEventName": "PreToolUse",
        "updatedInput": {**tool_input, "command": updated},
    }
    if only_admin:
        output["permissionDecision"] = "allow"
        output["permissionDecisionReason"] = "管理者が明示的に有効にした Git / Docker Compose の専用コマンドです。"
    return {"hookSpecificOutput": output}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    profile_file = root.parent / "profile"
    profile = profile_file.read_text().strip() if profile_file.exists() else ""
    if (root / ".standalone").exists() or profile == "work" or profile.startswith("work/"):
        print(json.dumps(handle(json.load(sys.stdin), root)))
    else:
        print("{}")
