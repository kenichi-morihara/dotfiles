#!/bin/bash

if [ "$(uname)" != "Linux" ] ; then
	echo "Not Linux!"
	exit 1
fi

# dotfilesディレクトリのscripts/linuxディレクトリのパスを取得
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGES_FILE="${SCRIPT_DIR}/.yay-packages.txt"

if [ ! -f "$PACKAGES_FILE" ]; then
	echo "Error: $PACKAGES_FILE not found"
	exit 1
fi

yay -S --needed - < "$PACKAGES_FILE"
