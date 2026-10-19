#!/bin/bash
# Checksum-pinned test dependency; does not modify the host package manager.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
version=2.73.2
case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) platform=darwin_arm64; checksum=b41f5a51700a7dc0b7c2ae02652d42824ee112d3d97cb2f3c725d53e8d9f6b32 ;;
    Darwin-x86_64) platform=darwin_amd64; checksum=c6c3e2a8eb3126c33cef454ad354e580d91290b92003c7bf21608d1e73832fc6 ;;
    Linux-x86_64) platform=linux_amd64; checksum=4d7bd8072f15373d5f5c801209bac218527452c8e54f9ae46ba6c5bd4a6eca41 ;;
    *) echo 'Unsupported test platform; install chezmoi yourself.' >&2; exit 1 ;;
esac
directory="$ROOT/.validation/tools/chezmoi-$version-$platform"
mkdir -p "$directory"
archive="$directory/chezmoi.tar.gz"
if [ ! -f "$archive" ]; then
    download=$(mktemp "$directory/download.XXXXXX")
    trap 'rm -f "$download"' EXIT
    curl -fsSL --retry 3 "https://github.com/twpayne/chezmoi/releases/download/v$version/chezmoi_${version}_${platform}.tar.gz" -o "$download"
    mv "$download" "$archive"
fi
python3 - "$archive" "$checksum" <<'PY'
import hashlib
from pathlib import Path
import sys
if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest() != sys.argv[2]:
    raise SystemExit('chezmoi archive checksum mismatch')
PY
tar -xzf "$archive" -C "$directory" chezmoi
printf '%s\n' "$directory/chezmoi"
