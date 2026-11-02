#!/bin/bash
# Docker Desktopのリソース設定を適用する。何度実行しても同じ状態になる。
#   .bin/macos/docker.sh          memoryMiBだけをsettings-store.jsonにマージ（初回のみ.bakを作成）
#   .bin/macos/docker.sh check    現在の値と期待値を比較（変更しない）
# 他のキーはDocker Desktopが管理するため、ファイル全体は配布せずjqで差分だけ書き換える。
# Docker Desktopは起動中に書き換えても反映されないので、適用後に再起動する。
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
    echo "Not macOS!" >&2
    exit 1
fi

# 割り当てメモリ(MiB)。TROCCOはapp/worker/webpack/DB/Redisなど多数のコンテナが動くため16GiB。
MEMORY_MIB="${DOCKER_MEMORY_MIB:-16384}"
SETTINGS_FILE="${DOCKER_SETTINGS_FILE:-$HOME/Library/Group Containers/group.com.docker/settings-store.json}"

mode="${1:-apply}"
case "$mode" in
    apply|check) ;;
    *) echo "Usage: $0 [check]" >&2; exit 2 ;;
esac

command -v jq >/dev/null || { echo "jq is required (brew install jq)" >&2; exit 1; }

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "settings-store.json not found: $SETTINGS_FILE" >&2
    echo "Docker Desktopを一度起動して初期設定を済ませてから再実行してください。" >&2
    exit 1
fi

current="$(jq -r '.memoryMiB // "unset"' "$SETTINGS_FILE")"

if [ "$current" = "$MEMORY_MIB" ]; then
    echo "ok   memoryMiB = $current"
    exit 0
fi

if [ "$mode" = "check" ]; then
    echo "DIFF memoryMiB: current=$current expected=$MEMORY_MIB"
    exit 1
fi

# 初回のみバックアップ（既存の.bakは上書きしない）
[ -e "$SETTINGS_FILE.bak" ] || cp -p "$SETTINGS_FILE" "$SETTINGS_FILE.bak"

tmp="$(mktemp "$SETTINGS_FILE.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
jq --argjson m "$MEMORY_MIB" '.memoryMiB = $m' "$SETTINGS_FILE" > "$tmp"
mv "$tmp" "$SETTINGS_FILE"
trap - EXIT

echo "set  memoryMiB: $current -> $MEMORY_MIB"
echo "Docker Desktopを再起動すると反映されます。"
