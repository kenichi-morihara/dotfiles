#!/bin/bash

if [ "$(uname)" != "Linux" ] ; then
	echo "Not Linux!"
	exit 1
fi

# dotfilesディレクトリの.binディレクトリのパスを取得
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGES_FILE="${SCRIPT_DIR}/.yay-packages.txt"

# 現在のパッケージリストをエクスポート
pacman -Qqe | sort > "$PACKAGES_FILE"

echo "Package list exported to: $PACKAGES_FILE"
echo "Total packages: $(wc -l < "$PACKAGES_FILE")"
