#!/usr/bin/env bash

set -euo pipefail

login_requested=false
if [[ "${1:-}" == "--login" ]]; then
  login_requested=true
fi

if ! command -v cursor >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    brew install --cask cursor
  else
    echo "cursor command is not installed. Install Cursor first: https://cursor.com/downloads"
    exit 1
  fi
fi

if ! cursor agent --version >/dev/null 2>&1; then
  echo "Installed Cursor does not provide 'cursor agent'. Update Cursor and retry."
  exit 1
fi

status_output=$(cursor agent status 2>&1 || true)
if ! grep -qi "not logged in" <<<"$status_output"; then
  echo "Cursor Agent is installed and authenticated."
  printf '%s\n' "$status_output"
  exit 0
fi

if [[ "$login_requested" == true ]]; then
  echo "Cursor Agent authentication is required. Complete the browser login."
  cursor agent login
  cursor agent status
else
  echo "Cursor Agent is installed but not authenticated."
  echo "Run: scripts/common/setup-cursor-agent.sh --login"
fi
