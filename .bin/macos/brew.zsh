# --- brew install/uninstall後に自動でBrewfileを更新 ---
# dotfilesディレクトリの.bin/macosディレクトリのパスを取得
# .zshrcがシンボリックリンクの場合、実パスを取得
if [[ -n "${(%):-%x}" ]]; then
  _DOTFILES_MACOS_DIR="${${(%):-%x}:A:h}"
  _DOTFILES_BIN_DIR="${_DOTFILES_MACOS_DIR:h}"
  _DOTFILES_DIR="${_DOTFILES_BIN_DIR:h}"
  BREWFILE_PATH="$_DOTFILES_MACOS_DIR/.Brewfile"
else
  # フォールバック: 環境変数や固定パスを使用
  _DOTFILES_DIR="${DOTFILES_DIR:-$HOME/ghq/github.com/kenichi-morihara/dotfiles}"
  BREWFILE_PATH="${_DOTFILES_DIR}/.bin/macos/.Brewfile"
fi

# 現在の upstream と同期する。作業中の変更や衝突を自動で上書きしない。
_brew_sync_dotfiles() {
  local current_branch=$(git branch --show-current)
  [[ "$current_branch" == "master" || "$current_branch" == "main" ]] || return 0

  if [[ -n "$(git ls-files -u)" ]] ||
     [[ -e "$(git rev-parse --git-path MERGE_HEAD)" ]] ||
     [[ -d "$(git rev-parse --git-path rebase-merge)" ]] ||
     [[ -d "$(git rev-parse --git-path rebase-apply)" ]]; then
    echo "⚠️  Git operation in progress; skipping automatic sync"
    return 1
  fi

  local upstream remote merge_ref
  upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}') || {
    echo "⚠️  No upstream configured; set one with git push -u"
    return 1
  }
  remote=$(git config --get "branch.$current_branch.remote") || return 1
  merge_ref=$(git config --get "branch.$current_branch.merge") || return 1
  git fetch "$remote" || return 1

  if ! git merge-base --is-ancestor "$upstream" HEAD; then
    if ! git diff --quiet || ! git diff --cached --quiet; then
      echo "⚠️  Tracked files have local changes; skipping automatic merge and push"
      return 1
    fi
    if ! GIT_MERGE_AUTOEDIT=no git merge --no-edit "$upstream"; then
      if [[ -e "$(git rev-parse --git-path MERGE_HEAD)" ]]; then
        git merge --abort || return 1
      fi
      echo "⚠️  Could not merge $upstream automatically; resolve manually and retry"
      return 1
    fi
  fi

  if git push "$remote" "HEAD:$merge_ref"; then
    echo "✅ Pushed to remote"
  else
    echo "⚠️  Push failed; the next successful brew install/uninstall/tap/untap will retry"
    return 1
  fi
}

# brewコマンドをラップする関数
brew() {
  local brew_cmd=$(whence -p brew)
  
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
    local brewfile_path="${BREWFILE_PATH:-${_DOTFILES_MACOS_DIR}/.Brewfile}"
    local dotfiles_dir="${_DOTFILES_DIR:-$(dirname "$(dirname "$brewfile_path")")}"
    
    # ディレクトリが存在する場合のみ実行
    if [[ -d "$(dirname "$brewfile_path")" ]] && [[ -d "$dotfiles_dir/.git" ]]; then
      # マージ・rebase 中のファイルを dump で上書きしない。
      if [[ -n "$(git -C "$dotfiles_dir" ls-files -u)" ]] ||
         [[ -e "$(git -C "$dotfiles_dir" rev-parse --absolute-git-dir)/MERGE_HEAD" ]] ||
         [[ -d "$(git -C "$dotfiles_dir" rev-parse --absolute-git-dir)/rebase-merge" ]] ||
         [[ -d "$(git -C "$dotfiles_dir" rev-parse --absolute-git-dir)/rebase-apply" ]]; then
        echo "⚠️  Git operation in progress; skipping Brewfile update and sync"
        return $exit_code
      fi

      local tmp_brewfile=$(mktemp)
      if ! command "$brew_cmd" bundle dump --file="$tmp_brewfile" --force; then
        rm -f "$tmp_brewfile"
        echo "⚠️  Failed to dump Brewfile; skipping commit and sync"
        return $exit_code
      fi
      cp "$tmp_brewfile" "$brewfile_path"
      
      # 変更があるか確認
      if [[ -f "$brewfile_path" ]]; then
        (
          cd "$dotfiles_dir" || return 1
          
          if [[ -n "$(git ls-files -u)" ]] ||
             [[ -e "$(git rev-parse --git-path MERGE_HEAD)" ]] ||
             [[ -d "$(git rev-parse --git-path rebase-merge)" ]] ||
             [[ -d "$(git rev-parse --git-path rebase-apply)" ]]; then
            echo "⚠️  Git operation in progress; skipping automatic commit and sync"
            return 1
          fi

          # git diffで変更があるか確認
          if ! git diff --quiet -- ".bin/macos/.Brewfile" 2>/dev/null; then
            # カラフルなdiffを表示
            echo ""
            echo "📦 Brewfile updated! Changes:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            git diff --color=always -- ".bin/macos/.Brewfile" || true
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            
            local current_branch=$(git branch --show-current)
            if [[ "$current_branch" == "master" || "$current_branch" == "main" ]]; then
              # 他の作業中の変更を自動コミットに含めない。
              if git commit --only -m "chore: update Brewfile [auto-commit]" -- .bin/macos/.Brewfile; then
                echo "✅ Committed to $current_branch"
              else
                echo "⚠️  Failed to commit Brewfile"
                return 1
              fi
            else
              echo "⚠️  Not on master/main branch (current: $current_branch), skipping commit"
            fi
          fi

          # Brewfile に差分がなくても、前回送信できなかったコミットを再試行する。
          _brew_sync_dotfiles
        )
      fi
      
      # 一時ファイルを削除
      [[ -f "$tmp_brewfile" ]] && rm -f "$tmp_brewfile"
    fi
  fi
  
  return $exit_code
}
