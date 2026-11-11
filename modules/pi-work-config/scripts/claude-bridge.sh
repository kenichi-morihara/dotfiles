#!/usr/bin/env bash
set -euo pipefail

# Authenticate through the official CLI's default login and ignore API/routing overrides.
while IFS= read -r name; do
  case "$name" in
    ANTHROPIC_* | CLAUDE_CODE_* | CLAUDE_CONFIG_DIR | CLAUDECODE) unset "$name" ;;
  esac
done < <(compgen -e)

# The bridge sends Pi's context over stdin. Keep Claude out of the calling repo.
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [ "${1:-}" = -p ]; then
  set -- "$@" --setting-sources ""
fi
exec claude "$@"
