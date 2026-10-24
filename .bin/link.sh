#!/bin/bash
# Compatibility entry point; chezmoi owns file deployment and persistent state.
set -euo pipefail
DOTFILES_DIR="$(cd "$(dirname "$0")/.." && pwd)"
chezmoi_bin="${CHEZMOI_BIN:-$(command -v chezmoi || true)}"
if [ -z "$chezmoi_bin" ]; then
    for candidate in /opt/homebrew/bin/chezmoi /usr/local/bin/chezmoi; do
        if [ -x "$candidate" ]; then chezmoi_bin="$candidate"; break; fi
    done
fi
if [ ! -x "$chezmoi_bin" ]; then
    echo 'Install chezmoi first (macOS: command brew install chezmoi).' >&2
    exit 127
fi
# Apply first so the one-time migration materializes an existing ~/.config
# symlink before init writes chezmoi's own configuration there.
"$chezmoi_bin" --source "$DOTFILES_DIR" --destination "$HOME" apply "$@"
exec "$chezmoi_bin" --source "$DOTFILES_DIR" --destination "$HOME" init "$@"
