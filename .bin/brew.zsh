# --- brew install/uninstall後に自動でBrewfileを更新 ---
# dotfilesディレクトリの.binディレクトリのパスを取得
# .zshrcがシンボリックリンクの場合、実パスを取得
if [[ -n "${(%):-%x}" ]]; then
  _DOTFILES_BIN_DIR="${${(%):-%x}:A:h}"
  _DOTFILES_DIR="${_DOTFILES_BIN_DIR:h}"
  BREWFILE_PATH="$_DOTFILES_BIN_DIR/.Brewfile"
else
  # フォールバック: 環境変数や固定パスを使用
  _DOTFILES_DIR="${DOTFILES_DIR:-$HOME/ghq/github.com/kenichi-morihara/dotfiles}"
  BREWFILE_PATH="${_DOTFILES_DIR}/.bin/.Brewfile"
fi

# brewコマンドをラップする関数
brew() {
  local brew_cmd=$(command -v brew)
  
  # brewコマンドが見つからない場合はエラー
  if [[ -z "$brew_cmd" ]]; then
    echo "Error: brew command not found" >&2
    return 1
  fi
  
  # 実際のbrewコマンドを実行
  command "$brew_cmd" "$@"
  local exit_code=$?
  
  # install, uninstall, tap, untap の後にBrewfileを更新
  if [[ $exit_code -eq 0 ]] && [[ "$1" =~ ^(install|uninstall|tap|untap)$ ]]; then
    local brewfile_path="${BREWFILE_PATH:-${_DOTFILES_BIN_DIR}/.Brewfile}"
    local dotfiles_dir="${_DOTFILES_DIR:-$(dirname "$(dirname "$brewfile_path")")}"
    
    # ディレクトリが存在する場合のみ実行
    if [[ -d "$(dirname "$brewfile_path")" ]] && [[ -d "$dotfiles_dir/.git" ]]; then
      # 一時的にBrewfileをバックアップ
      local tmp_brewfile=$(mktemp)
      [[ -f "$brewfile_path" ]] && cp "$brewfile_path" "$tmp_brewfile"
      
      # Brewfileを更新
      command "$brew_cmd" bundle dump --file="$brewfile_path" --force 2>/dev/null || true
      
      # 変更があるか確認
      if [[ -f "$brewfile_path" ]]; then
        (
          cd "$dotfiles_dir" || return 1
          
          # git diffで変更があるか確認
          if ! git diff --quiet -- ".bin/.Brewfile" 2>/dev/null; then
            # カラフルなdiffを表示
            echo ""
            echo "📦 Brewfile updated! Changes:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            git diff --color=always -- ".bin/.Brewfile" || true
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            
            # git add, commit, push
            local current_branch=$(git branch --show-current 2>/dev/null || echo "master")
            if [[ "$current_branch" == "master" ]] || [[ "$current_branch" == "main" ]]; then
              git add ".bin/.Brewfile" 2>/dev/null || true
              local commit_msg="chore: update Brewfile [auto-commit]"
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
      [[ -f "$tmp_brewfile" ]] && rm -f "$tmp_brewfile"
    fi
  fi
  
  return $exit_code
}
