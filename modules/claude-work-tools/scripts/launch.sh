#!/usr/bin/env bash
# dotfiles Claude admin launcher
set -euo pipefail

config="${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles"
root="$config/claude-admin"
case "$(cat "$config/profile" 2>/dev/null || true)" in
  work | work/*) ;;
  *) if [ ! -f "$root/.standalone" ]; then echo 'claude-admin は会社用 profile 専用です。' >&2; exit 1; fi ;;
esac

for file in settings.json prompt.txt tools.json rewrite.py bin/admin-git bin/admin-compose .venv/bin/python; do
  if [ ! -r "$root/$file" ]; then
    echo 'make claude-admin-setup を実行してください。' >&2
    exit 1
  fi
done

echo '[claude-admin] Git と Docker Compose は管理者用コマンドへ変換して自動許可します。' >&2
exec claude --settings "$root/settings.json" --append-system-prompt "$(cat "$root/prompt.txt")" "$@"
