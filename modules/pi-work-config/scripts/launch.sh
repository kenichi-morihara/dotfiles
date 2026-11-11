#!/usr/bin/env bash
# dotfiles company Pi launcher
set -euo pipefail

config="${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles"
root="$config/pi"
runtime="$root/runtime-1.5.1-1.2.1"
claude_bridge="$root/claude-bridge"
provider="$runtime/node_modules/claude-code-pi/src/index.ts"

case "$(cat "$config/profile" 2>/dev/null || true)" in
  work | work/*) ;;
  *)
    if [ ! -f "$root/.standalone" ]; then
    while IFS= read -r candidate; do
      if [ ! "$candidate" -ef "$0" ]; then exec "$candidate" "$@"; fi
    done < <(type -aP pi)
    echo '通常の pi が見つかりません。会社用 Pi を使うには会社用プロファイルを選択してください。' >&2
    exit 127
    fi
    ;;
esac
umask 077

# Keep the launcher's provider, extension, trust and session settings authoritative.
for arg in "$@"; do
  case "$arg" in
    -p | --print | --no-session | -c | --continue | -r | --resume | --verbose | --no-tools | --version | -v) ;;
    -*) printf '会社用ランチャーでは指定できないオプションです: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

export PI_CODING_AGENT_DIR="$root/agent"
unset PI_CODING_AGENT_SESSION_DIR PI_PACKAGE_DIR CLAUDE_CODE_PI_MODELS
export CLAUDE_CODE_PI_BIN="$claude_bridge"

if [ ! -x "$runtime/node_modules/.bin/pi" ] || [ ! -r "$provider" ] ||
   [ ! -x "$claude_bridge" ] || [ ! -r "$PI_CODING_AGENT_DIR/settings.json" ]; then
  echo '会社用 Pi の導入が不完全です。対応する make pi-setup を実行してください。' >&2
  exit 1
fi

if ! "$claude_bridge" auth status --json | node -e '
  try {
    const status = JSON.parse(require("node:fs").readFileSync(0, "utf8"));
    if (status.loggedIn !== true || status.authMethod !== "claude.ai" ||
        status.apiProvider !== "firstParty" || status.subscriptionType !== "team") {
      process.exitCode = 1;
    }
  } catch {
    process.exitCode = 1;
  }
'; then
  echo 'Claude Team のログインを確認できません。公式 CLI の claude auth status を確認してください。' >&2
  exit 1
fi

echo '[pi] 会社用: Pi の標準ツールは確認なしで実行されます。' >&2

exec "$runtime/node_modules/.bin/pi" --no-approve --no-extensions --no-mcp \
  --model claude-code-cli/sonnet --models 'claude-code-cli/*' -e "$provider" "$@"
