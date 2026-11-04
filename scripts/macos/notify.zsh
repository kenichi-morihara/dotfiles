# --- パイプ左のコマンドを保存 ---
LAST_PIPELINE_CMD=""

notify_preexec() {
  # 例: "ls -al | notify"
  LAST_PIPELINE_CMD=$(echo "$1" | sed 's/| *notify.*//')
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec notify_preexec


# --- notify 本体（リアルタイム表示対応） ---
_notify_func() {
  local tmpfile title msg exit_code icon

  # 一時ファイルに出力を保存
  tmpfile=$(mktemp)

  # 標準入力をリアルタイムで画面に表示しつつ tmpfile にコピー
  tee "$tmpfile"

  # パイプ左のコマンド終了ステータスを取得
  exit_code=${PIPESTATUS[0]:-$?}  # パイプ左のステータスを優先

  # 成功/失敗でアイコンを設定
  if [ $exit_code -eq 0 ]; then
    icon="✅"
  else
    icon="❌"
  fi

  # タイトルと通知用メッセージ
  title="$icon $LAST_PIPELINE_CMD"
  msg=$(tail -n 5 "$tmpfile" | tr '\n' ' ')

  terminal-notifier -title "$title" -message "$msg"

  # 一時ファイル削除
  rm "$tmpfile"
}

# --- alias で notify として使う ---
alias notify='noglob _notify_func'
