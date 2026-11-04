#!/bin/bash
# Apply independent app settings, collecting failures without stopping later apps.
set -euo pipefail
[ "$(uname -s)" = Darwin ] || { echo "Not macOS!" >&2; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mode="${1:-apply}"
case "$mode" in apply) args=() ;; --check) args=(--check) ;; *) echo "Usage: $0 [--check]" >&2; exit 2 ;; esac
failures=()
applications_dir="${DOTFILES_APPLICATIONS_DIR:-/Applications}"
run_app() {
    local name="$1" app="$2"
    shift 2
    if [ ! -d "$applications_dir/$app.app" ] && [ ! -d "$HOME/Applications/$app.app" ]; then
        echo "SKIP $name: not installed"
        return
    fi
    if "$@" ${args[@]+"${args[@]}"}; then
        :
    else
        failures+=("$name")
    fi
}
run_app Rectangle Rectangle bash "$SCRIPT_DIR/rectangle.sh"
run_app Nani Nani "${PYTHON:-python3}" "$SCRIPT_DIR/nani.py"
run_app iTerm2 iTerm "${PYTHON:-python3}" "$SCRIPT_DIR/iterm2.py"
if [ -d "/Library/Input Methods/GoogleJapaneseInput.app" ]; then
    if swift "$SCRIPT_DIR/input-sources.swift" "$SCRIPT_DIR/input-sources.json" ${args[@]+"${args[@]}"}; then
        :
    else
        failures+=("Input sources")
    fi
else
    echo "SKIP Google IME: not installed"
fi
if [ "${#failures[@]}" -gt 0 ]; then
    printf 'Failed: %s\n' "${failures[@]}" >&2
    exit 1
fi
