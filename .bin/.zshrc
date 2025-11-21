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

## abbr
abbr -S goto='cd "$(ghq list --full-path | peco)"'
abbr -S reload='exec $SHELL -l'

abbr -S l='exa -F'
abbr -S ll='exa -Fl'
abbr -S la='exa -Fa'
abbr -S lla='exa -Fla'
abbr -S v='vim'
abbr -S g='git'
abbr -S b='bat'
abbr -S venv='source venv/bin/activate'
abbr -S ra='rails'
abbr -S gr='grep'
abbr -S k='kubectl'
abbr -S t='tmux'

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
