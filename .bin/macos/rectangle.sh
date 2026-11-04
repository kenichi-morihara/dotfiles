#!/bin/bash
# Apply the Rectangle shortcuts declared below. Safe to run repeatedly.
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
    echo "Not macOS!" >&2
    exit 1
fi

mode="${1:-apply}"
case "$mode" in apply|--check) ;; *) echo "Usage: $0 [--check]" >&2; exit 2 ;; esac
SHORTCUTS='leftHalf 123 1835008
rightHalf 124 1835008
maximize 126 1835008
restore 125 1835008
previousDisplay 123 1966080
nextDisplay 124 1966080'
# Compare before backing up, writing or restarting. A check never mutates preferences.
if "${PYTHON:-python3}" - "$SHORTCUTS" <<'PY_CHECK'
import plistlib, subprocess, sys
result = subprocess.run(['defaults', 'export', 'com.knollsoft.Rectangle', '-'], capture_output=True)
try:
    current = plistlib.loads(result.stdout) if result.returncode == 0 else {}
except plistlib.InvalidFileException as error:
    print(f'Cannot read Rectangle preferences: {error}', file=sys.stderr)
    sys.exit(2)
for line in sys.argv[1].splitlines():
    action, key, flags = line.split()
    value = current.get(action, {})
    if value.get('keyCode') != int(key) or value.get('modifierFlags') != int(flags):
        sys.exit(1)
PY_CHECK
then
    echo "Rectangle shortcuts already match."
    exit 0
else
    result=$?
    [ "$result" -eq 1 ] || exit "$result"
fi
if [ "$mode" = --check ]; then
    echo "Rectangle shortcuts differ."
    exit 1
fi

domain=com.knollsoft.Rectangle
backup_dir="$HOME/Library/Application Support/Rectangle/dotfiles-backups"
mkdir -p "$backup_dir"
backup=$(mktemp "$backup_dir/preferences.XXXXXX")
if defaults read "$domain" >/dev/null 2>&1; then
    defaults export "$domain" "$backup"
    echo "Backup: $backup"
else
    rm -f "$backup"
fi

# Stop the app before changing NSUserDefaults so cached values cannot overwrite them.
was_running=false
if pgrep -x Rectangle >/dev/null; then
    was_running=true
    osascript -e 'tell application "Rectangle" to quit'
    for ((attempt = 0; attempt < 50; attempt++)); do
        if ! pgrep -x Rectangle >/dev/null; then
            break
        fi
        sleep 0.1
    done
    if pgrep -x Rectangle >/dev/null; then
        echo "Rectangle did not quit; settings were not changed." >&2
        exit 1
    fi
fi

# Cocoa modifierFlags: Control=262144, Option=524288, Command=1048576,
# Shift=131072. Arrow keyCodes: left=123, right=124, down=125, up=126.
while read -r action key_code modifier_flags; do
    defaults write "$domain" "$action" -dict \
        keyCode -int "$key_code" modifierFlags -int "$modifier_flags"
done <<<"$SHORTCUTS"

if [ "$was_running" = true ]; then
    open -a Rectangle
fi
echo "Rectangle shortcuts applied."
