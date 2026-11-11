#!/bin/bash
set -euo pipefail
[ "$(uname -s)" = Darwin ] || { echo 'Not macOS!' >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
args=()
if [ "${1:-}" = --check ]; then args=(--check); fi
failures=0
if [ -d /Applications/Nani.app ] || [ -d "$HOME/Applications/Nani.app" ]; then
  "${PYTHON:-python3}" "$HERE/macos/nani.py" "${args[@]}" || failures=1
fi
if [ -d "/Library/Input Methods/GoogleJapaneseInput.app" ]; then
  swift "$HERE/macos/input-sources.swift" "$HERE/macos/input-sources.json" "${args[@]}" || failures=1
fi
exit "$failures"
