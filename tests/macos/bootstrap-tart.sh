#!/bin/bash
# Install a checksum-pinned Tart into repo-local ignored storage.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
    echo 'Tart validation requires an Apple Silicon Mac.' >&2
    exit 1
fi
version=2.41.1
checksum=e680a734febccfce7d4e910c1f7f13fc3b00f19a181c945e2d746de3214c32c2
cache="$ROOT/.validation/tools"
archive="$cache/tart-$version.tar.gz"
install_dir="$cache/tart-$version"
mkdir -p "$cache"
if [ ! -f "$archive" ]; then
    download=$(mktemp "$cache/download.XXXXXX")
    trap 'rm -f "$download"' EXIT
    curl -fsSL --retry 3 "https://github.com/cirruslabs/tart/releases/download/$version/tart.tar.gz" -o "$download"
    printf '%s  %s\n' "$checksum" "$download" | shasum -a 256 -c - >/dev/null
    mv "$download" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | shasum -a 256 -c - >/dev/null
mkdir -p "$install_dir"
tar -xzf "$archive" -C "$install_dir"
printf '%s\n' "$install_dir/tart.app/Contents/MacOS/tart"
