#!/usr/bin/env bash
# Install one company Pi launcher and the shared, pinned runtime.
set -euo pipefail
umask 077

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles"
PROFILE_FILE="$CONFIG_DIR/profile"
ROOT="$CONFIG_DIR/pi"
PI_PACKAGE="@earendil-works/pi-coding-agent"
BRIDGE_PACKAGE="claude-code-pi"
PI_VERSION="1.5.1"
BRIDGE_VERSION="1.2.1"
RUNTIME="$ROOT/runtime-$PI_VERSION-$BRIDGE_VERSION"

AGENT_DIR="$ROOT/agent"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/pi"

profile="$(cat "$PROFILE_FILE" 2>/dev/null || true)"
case "$profile" in
  work | work/*) ;;
  *)
    if [ "${STANDALONE:-0}" = 1 ]; then
      profile=standalone
    else
    echo "pi のセットアップは会社用 profile 専用です（現在: ${profile:-未選択}）。make profile-select で会社用を選んでください。" >&2
    exit 1
    fi
    ;;
esac

if { [ -e "$LAUNCHER" ] || [ -L "$LAUNCHER" ]; } &&
   ! grep -Fxq '# dotfiles company Pi launcher' "$LAUNCHER"; then
  printf '既存の %s を確認してください。会社用ランチャーを導入できません。\n' "$LAUNCHER" >&2
  exit 1
fi

if ! mise exec -- node -e 'const [a, b] = process.versions.node.split(".").map(Number); process.exit(a > 22 || (a === 22 && b >= 19) ? 0 : 1)'; then
  echo "pi には Node.js 22.19 以上が必要です。make runtimes を実行してください。" >&2
  exit 1
fi

mkdir -p "$ROOT"
if ! mkdir "$ROOT/.install-lock" 2>/dev/null; then
  echo "会社用 Pi の導入ロックを取得できません: $ROOT/.install-lock" >&2
  exit 1
fi
stage=""
cleanup() {
  if [ -n "$stage" ]; then rm -rf -- "$stage"; fi
  rmdir "$ROOT/.install-lock"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

if [ ! -x "$RUNTIME/node_modules/.bin/pi" ] ||
   [ ! -f "$RUNTIME/node_modules/$BRIDGE_PACKAGE/src/index.ts" ]; then
  if [ -e "$RUNTIME" ]; then
    echo "会社用 Pi のランタイムが不完全です: $RUNTIME" >&2
    exit 1
  fi
  echo "==> pi $PI_VERSION / $BRIDGE_PACKAGE $BRIDGE_VERSION"
  stage="$(mktemp -d "$ROOT/.runtime.XXXXXXXX")"
  mise exec -- npm install --prefix "$stage" --ignore-scripts --no-save --no-package-lock \
    "$PI_PACKAGE@$PI_VERSION" "$BRIDGE_PACKAGE@$BRIDGE_VERSION"
  test -x "$stage/node_modules/.bin/pi"
  test -f "$stage/node_modules/$BRIDGE_PACKAGE/src/index.ts"
  mv -- "$stage" "$RUNTIME"
  stage=""
fi

if [ ! -e "$AGENT_DIR" ] && [ -d "$ROOT/lead" ]; then
  mv -- "$ROOT/lead" "$AGENT_DIR"
fi
mkdir -p "$AGENT_DIR" "$BIN_DIR"
if [ "$profile" = standalone ]; then printf 'enabled\n' > "$ROOT/.standalone"; fi
install -m 700 "$HERE/claude-bridge.sh" "$ROOT/claude-bridge"
if [ ! -f "$AGENT_DIR/settings.json" ]; then
  install -m 600 "$HERE/agent/settings.json" "$AGENT_DIR/settings.json"
fi
install -m 700 "$HERE/launch.sh" "$LAUNCHER"

archive=""
for previous in "$ROOT/member" "$ROOT/lead" "$BIN_DIR/pi-work" "$BIN_DIR/pi-work-lead"; do
  if [ -e "$previous" ] || [ -L "$previous" ]; then
    if [ -z "$archive" ]; then
      archive="$(mktemp -d "$CONFIG_DIR/pi-retired.XXXXXXXX")"
      printf '旧構成の退避先: %s\n' "$archive"
    fi
    mv -- "$previous" "$archive/"
  fi
done
printf '完了。会社用 Claude Team にログインした状態で pi を実行してください。\n'
