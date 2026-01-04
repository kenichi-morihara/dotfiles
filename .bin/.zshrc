#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# ============================================
# zinit プラグイン管理
# ============================================
source /opt/homebrew/opt/zinit/zinit.zsh
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit

# ZENO_HOMEはzeno.zsh読み込み前に設定する必要がある
export ZENO_HOME=~/.config/zeno

# zeno.zsh（fast-syntax-highlightingより先に読み込む必要がある）
zinit ice lucid depth"1" blockf
zinit light yuki-yano/zeno.zsh

# Prezto の代わりとなるプラグイン
# 基本機能（Oh My Zshのライブラリ）
zinit ice wait lucid
zinit snippet OMZ::lib/git.zsh

# 履歴検索（fast-syntax-highlightingより先に読み込む必要がある）
zinit ice wait lucid
zinit light zsh-users/zsh-history-substring-search

# シンタックスハイライト（高速版）
zinit ice wait lucid atinit'zpcompinit; zpcdreplay'
zinit light zdharma-continuum/fast-syntax-highlighting

# 自動補完提案
zinit ice wait lucid atload'!_zsh_autosuggest_start'
zinit light zsh-users/zsh-autosuggestions

# 補完機能強化
zinit ice wait lucid blockf
zinit light zsh-users/zsh-completions

# ディレクトリ移動機能
zinit ice wait lucid
zinit light skywind3000/z.lua

# Git関連プラグイン
zinit ice wait"2" lucid as"null" sbin
zinit light paulirish/git-open

zinit ice wait"2" lucid as"null" sbin
zinit light paulirish/git-recent

# 便利コマンド
zinit ice wait lucid
zinit snippet OMZ::plugins/sudo/sudo.plugin.zsh

zinit ice wait lucid
zinit snippet OMZ::plugins/extract/extract.plugin.zsh

# fzf（あいまい検索）
zinit ice wait lucid
zinit light junegunn/fzf

# fzf-tab（タブ補完をfzfで表示）
# zeno-completionを使用する場合はコメントアウト（zenoの補完と競合する可能性がある）
zinit ice wait lucid
zinit light Aloxaf/fzf-tab

# ============================================
# Prezto（コメントアウト - 必要に応じて戻す）
# ============================================
# if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
#   source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
# fi

# Customize to your needs...
eval "$(starship init zsh)"
eval "$(fnm env --use-on-cd)"

# Keybindings
# 文節単位で採用（Alt+→）
bindkey '\ef' forward-word  # Alt+F（デフォルト）
# または
bindkey '^[[1;3C' forward-word  # Alt+→

# 履歴検索のキーバインド（zsh-history-substring-search用）
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down


### zeno
# if disable deno cache command when plugin loaded
# export ZENO_DISABLE_EXECUTE_CACHE_COMMAND=1

# if enable fzf-tmux
# export ZENO_ENABLE_FZF_TMUX=1

# if setting fzf-tmux options
# export ZENO_FZF_TMUX_OPTIONS="-p"

# by default a unix domain socket is used
# if disable it
# export ZENO_DISABLE_SOCK=1

# if disable builtin completion
# export ZENO_DISABLE_BUILTIN_COMPLETION=1

# default
export ZENO_GIT_CAT="cat"
# git file preview with color
# export ZENO_GIT_CAT="bat --color=always"

# default
export ZENO_GIT_TREE="tree"
# git folder preview with color
# export ZENO_GIT_TREE="eza --tree"

if [[ -n $ZENO_LOADED ]]; then
  bindkey ' '  zeno-auto-snippet

  # fallback if snippet not matched (default: self-insert)
  # export ZENO_AUTO_SNIPPET_FALLBACK=self-insert

  # if you use zsh's incremental search
  # bindkey -M isearch ' ' self-insert

  # bindkey '^m' zeno-auto-snippet-and-accept-line

  bindkey '^g' zeno-ghq-cd
  bindkey '^i' zeno-completion

  bindkey '^xx' zeno-insert-snippet           # open snippet picker (fzf) and insert at cursor

  bindkey '^x '  zeno-insert-space
  bindkey '^x^m' accept-line
  bindkey '^x^z' zeno-toggle-auto-snippet

  # preprompt bindings
  bindkey '^xp' zeno-preprompt
  bindkey '^xs' zeno-preprompt-snippet
  # Outside ZLE you can run `zeno-preprompt git {{cmd}}` or `zeno-preprompt-snippet foo`
  # to set the next prompt prefix; invoking them with an empty argument resets the state.

  bindkey '^h' zeno-history-selection         # classic history widget
  # bindkey '^r' zeno-smart-history-selection # smart history widget

  # fallback if completion not matched
  # (default: fzf-compdletion if exists; otherwise expand-or-complete)
  # export ZENO_COMPLETION_FALLBACK=expand-or-complete
fi

# fzf-tabはzeno-completionと競合するため無効化
# zsh-autocompleteと組み合わせる場合、いい感じに補完をするために以下の設定を追加
# my-fzf-tab() {
#   functions[compadd]=$functions[-ftb-compadd]
#   zle fzf-tab-complete
# }
# zle -N my-fzf-tab
# bindkey "^I" my-fzf-tab

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