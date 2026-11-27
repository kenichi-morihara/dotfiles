#!/usr/bin/env bash
# Add the rustup components that rust-analyzer (editor / Claude Code LSP) needs.
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles"
PROFILE_FILE="$CONFIG_DIR/profile"
# rust-analyzer: ~/.cargo/bin/rust-analyzer は rustup のシムで、本体が無いと起動に失敗する。
# rust-src: 標準ライブラリの補完・型解析に使う。
COMPONENTS=(rust-analyzer rust-src)

profile="$(cat "$PROFILE_FILE" 2>/dev/null || true)"
case "$profile" in
  work | work/*) ;;
  *)
    echo "rust-analyzer のセットアップは会社用 profile 専用です（現在: ${profile:-未選択}）。make profile-select で会社用を選んでください。" >&2
    exit 1
    ;;
esac

if ! command -v rustup >/dev/null 2>&1; then
  echo "rustup が見つかりません。https://rustup.rs の手順で Rust を導入してから再実行してください。" >&2
  exit 1
fi

rustup component add "${COMPONENTS[@]}"
rust-analyzer --version
