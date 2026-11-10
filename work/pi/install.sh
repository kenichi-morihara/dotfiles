#!/usr/bin/env bash
# Install pi coding agent and the Claude-compatible permission extension (work profile only).
# Run: make pi-setup
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles/profile"
AGENT_DIR="$HOME/.pi/agent"
PACKAGE="@earendil-works/pi-coding-agent"

profile="$(cat "$PROFILE_FILE" 2>/dev/null || true)"
if [ -z "$profile" ] && [ -t 0 ] && [ -t 1 ]; then
  echo "profile が未選択です。pi は会社用 profile で使います。"
  "${PYTHON:-python3}" "$HERE/../../scripts/common/profiles.py" select
  profile="$(cat "$PROFILE_FILE" 2>/dev/null || true)"
fi
case "$profile" in
  work | work/*) ;;
  *)
    echo "pi のセットアップは会社用 profile 専用です（現在: ${profile:-未選択}）。make profile-select で会社用を選んでください。" >&2
    exit 1
    ;;
esac

if ! mise exec -- node -e 'const [a, b] = process.versions.node.split(".").map(Number); process.exit(a > 22 || (a === 22 && b >= 19) ? 0 : 1)'; then
  echo "pi には Node.js 22.19 以上が必要です。make runtimes を実行してください。" >&2
  exit 1
fi

echo "==> pi ($PACKAGE)"
mise exec -- npm install -g --ignore-scripts "$PACKAGE"

echo "==> pi 設定 ($AGENT_DIR)"
install_file() {
  local source="$1" target="$2"
  mkdir -p "$(dirname "$target")"
  if [ -f "$target" ] && ! cmp -s "$source" "$target"; then
    cp -p "$target" "$target.backup"
    echo "    退避: $target.backup"
  fi
  cp "$source" "$target"
  echo "    配置: $target"
}
install_file "$HERE/agent/settings.json" "$AGENT_DIR/settings.json"
for file in index.ts rules.ts; do
  install_file "$HERE/agent/extensions/claude-permissions/$file" "$AGENT_DIR/extensions/claude-permissions/$file"
done

echo "完了。ログインは pi を起動して /login で本人が行ってください（auth.json は Git 管理しません）。"
