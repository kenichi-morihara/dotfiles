#!/bin/bash
# Keep app-specific implementations behind one entry point.
set -euo pipefail

if [ "$(uname -s)" != Darwin ]; then
    echo "Not macOS!" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$SCRIPT_DIR/rectangle.sh"
"${PYTHON:-python3}" "$SCRIPT_DIR/nani.py"
"${PYTHON:-python3}" "$SCRIPT_DIR/iterm2.py"
