# Fig pre block. Keep at the top of this file.
[[ -f "$HOME/.fig/shell/zshrc.pre.zsh" ]] && builtin source "$HOME/.fig/shell/zshrc.pre.zsh"
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
export PATH="~/.rbenv/shims:/usr/local/bin:$PATH"
eval "$(rbenv init -)"
# eval "$(nodenv init -)"

## alias
alias goto='cd "$(ghq list --full-path | peco)"'

# Fig post block. Keep at the bottom of this file.
[[ -f "$HOME/.fig/shell/zshrc.post.zsh" ]] && builtin source "$HOME/.fig/shell/zshrc.post.zsh"
