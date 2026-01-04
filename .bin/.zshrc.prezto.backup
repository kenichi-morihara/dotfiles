#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Source Prezto.
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi

# Customize to your needs...
eval "$(starship init zsh)"
eval "$(fnm env --use-on-cd)"

## zsh-abbr
source /opt/homebrew/opt/zsh-abbr/share/zsh-abbr/zsh-abbr.zsh

## zeno.sh
# zeno.zsh の読み込み
source /Users/kenichi.morihara/ghq/github.com/kenichi-morihara/dotfiles/.bin/zeno.zsh/zeno.zsh
# エラーが発生しても ZENO_LOADED を設定（zeno の基本機能は動作する）
if [[ -z $ZENO_LOADED ]] && command -v deno >/dev/null 2>&1; then
  export ZENO_LOADED=1
  export ZENO_ENABLE=1
fi

abbr -S goto='cd "$(ghq list --full-path | peco)"'
abbr -S reload='exec $SHELL -l'

# abbr -S l='exa -F'
# abbr -S ll='exa -Fl'
# abbr -S la='exa -Fa'
# abbr -S lla='exa -Fla'
abbr -S v='vim'
abbr -S g='git'
abbr -S b='bat'
# abbr -S venv='source venv/bin/activate'
# abbr -S ra='rails'
abbr -S gr='grep'
# abbr -S k='kubectl'
# abbr -S t='tmux'

# docker
abbr -S d='docker'
abbr -S dps='docker container ls'
abbr -S dimgs='docker image ls'
abbr -S drun='docker container run'
abbr -S dcd='docker compose -d'

# git
abbr -S ga='git add'
abbr -S gacm='git add -A && git commit'
abbr -S gst='git status'
abbr -S gbr='git branch'
abbr -S gcm='git commit'
abbr -S gco='git checkout'
abbr -S gdf='git diff'
abbr -S gl='git log'
abbr -S ggr='git grep'
abbr -S gul='git pull'
abbr -S gsw='git switch'
abbr -S gush='git push'
abbr -S gget='ghq get'


# Keybindings
# 文節単位で採用（Alt+→）
bindkey '\ef' forward-word  # Alt+F（デフォルト）
# または
bindkey '^[[1;3C' forward-word  # Alt+→


### zeno
# if defined load the configuration file from there
# export ZENO_HOME=~/.config/zeno

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

  bindkey '^m' zeno-auto-snippet-and-accept-line

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

  bindkey '^r' zeno-history-selection         # classic history widget
  # bindkey '^r' zeno-smart-history-selection # smart history widget

  # fallback if completion not matched
  # (default: fzf-completion if exists; otherwise expand-or-complete)
  # export ZENO_COMPLETION_FALLBACK=expand-or-complete
fi