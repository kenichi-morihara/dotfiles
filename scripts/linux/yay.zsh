# --- yay install/uninstall後に自動でパッケージリストを更新 ---
# dotfilesディレクトリのscripts/linuxディレクトリのパスを取得
# .zshrcがシンボリックリンクの場合、実パスを取得
if [[ -n "${(%):-%x}" ]]; then
  _DOTFILES_LINUX_DIR="${${(%):-%x}:A:h}"
  _DOTFILES_SCRIPTS_DIR="${_DOTFILES_LINUX_DIR:h}"
  _DOTFILES_DIR="${_DOTFILES_SCRIPTS_DIR:h}"
  PACKAGES_FILE_PATH="$_DOTFILES_LINUX_DIR/.yay-packages.txt"
else
  # フォールバック: 環境変数や固定パスを使用
  _DOTFILES_DIR="${DOTFILES_DIR:-$HOME/ghq/github.com/kenichi-morihara/dotfiles}"
  PACKAGES_FILE_PATH="${_DOTFILES_DIR}/scripts/linux/.yay-packages.txt"
fi

# yayコマンドをラップする関数
yay() {
  local yay_cmd=$(command -v yay)
  
  # yayコマンドが見つからない場合はエラー
  if [[ -z "$yay_cmd" ]]; then
    echo "Error: yay command not found" >&2
    return 1
  fi
  
  # 実際のyayコマンドを実行
  command "$yay_cmd" "$@"
  local exit_code=$?
  
  # パッケージ変更コマンドの後にパッケージリストを更新
  # -S: インストール, -R: 削除, -Rs: 削除（依存関係も）, -Syu: アップグレード, -U: ローカルインストール
  if [[ $exit_code -eq 0 ]] && [[ "$1" =~ ^(-S|-R|-Rs|-Syu|-U)$ ]]; then
    local packages_file="${PACKAGES_FILE_PATH:-${_DOTFILES_LINUX_DIR}/.yay-packages.txt}"
    local dotfiles_dir="${_DOTFILES_DIR:-$(dirname "$(dirname "$packages_file")")}"
    
    # ディレクトリが存在する場合のみ実行
    if [[ -d "$(dirname "$packages_file")" ]] && [[ -d "$dotfiles_dir/.git" ]]; then
      # 一時的にパッケージリストをバックアップ
      local tmp_packages=$(mktemp)
      [[ -f "$packages_file" ]] && cp "$packages_file" "$tmp_packages"
      
      # パッケージリストを更新（明示的にインストールされたパッケージのみ）
      pacman -Qqe | sort > "$packages_file" 2>/dev/null || true
      
      # 変更があるか確認
      if [[ -f "$packages_file" ]]; then
        (
          cd "$dotfiles_dir" || return 1
          
          # git diffで変更があるか確認
          if ! git diff --quiet -- "scripts/linux/.yay-packages.txt" 2>/dev/null; then
            # カラフルなdiffを表示
            echo ""
            echo "📦 Package list updated! Changes:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            git diff --color=always -- "scripts/linux/.yay-packages.txt" || true
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            
            # git add, commit, push
            local current_branch=$(git branch --show-current 2>/dev/null || echo "master")
            if [[ "$current_branch" == "master" ]] || [[ "$current_branch" == "main" ]]; then
              git add "scripts/linux/.yay-packages.txt" 2>/dev/null || true
              local commit_msg="chore: update package list [auto-commit]"
              if git commit -m "$commit_msg" 2>/dev/null; then
                echo "✅ Committed to $current_branch"
                if git push 2>/dev/null; then
                  echo "✅ Pushed to remote"
                else
                  echo "⚠️  Failed to push (you may need to push manually)"
                fi
              else
                echo "⚠️  Failed to commit (no changes or git error)"
              fi
            else
              echo "⚠️  Not on master/main branch (current: $current_branch), skipping commit"
            fi
          fi
        )
      fi
      
      # 一時ファイルを削除
      [[ -f "$tmp_packages" ]] && rm -f "$tmp_packages"
    fi
  fi
  
  return $exit_code
}
