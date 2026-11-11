#!/bin/bash
# Compatibility entry point.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export DOTFILES_REPO_ROOT="$ROOT"
exec bash "$ROOT/modules/macos-preferences/scripts/macos/setup.sh" "$@"
