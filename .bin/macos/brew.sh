#!/bin/bash

if [ "$(uname)" != "Darwin" ] ; then
	echo "Not macOS!"
	exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
profile=full
if [ "${1:-}" = "--profile" ]; then
	profile="${2:-}"
	if [ "$#" -lt 2 ]; then
		echo "Usage: $0 [--profile core|full] [brew bundle arguments...]" >&2
		exit 2
	fi
	shift 2
fi

case "$profile" in
	core) brewfile="$SCRIPT_DIR/.Brewfile.core" ;;
	full) brewfile="$SCRIPT_DIR/.Brewfile" ;;
	*) echo "Unknown profile: $profile (expected core or full)" >&2; exit 2 ;;
esac

command brew bundle --file="$brewfile" "$@"
