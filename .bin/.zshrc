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

# export PATH="$HOME/.nodenv/bin:$PATH"

# Customize to your needs...
eval "$(starship init zsh)"
eval "$(fnm env --use-on-cd)"

# rbenv
# export PATH="~/.rbenv/shims:/usr/local/bin:$PATH"
# eval "$(rbenv init -)"
# eval "$(nodenv init -)"

# pyenv
# export PATH="$HOME/.pyenv/bin:$PATH"
# eval "$(pyenv init -)"
# eval "$(pyenv virtualenv-init -)"

## alias
alias goto='cd "$(ghq list --full-path | peco)"'
alias refresh='exec $SHELL -l'

# Fig post block. Keep at the bottom of this file.
[[ -f "$HOME/.fig/shell/zshrc.post.zsh" ]] && builtin source "$HOME/.fig/shell/zshrc.post.zsh"
