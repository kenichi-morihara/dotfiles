# Keybindings
# 文節単位で採用（Alt+→）
bindkey '\ef' forward-word  # Alt+F（デフォルト）
# または
bindkey '^[[1;3C' forward-word  # Alt+→

# 履歴検索のキーバインド（zsh-history-substring-search用）
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

# reload shell with ctrl+r (outside zeno block to ensure it's bound)
# remove default history search binding first
bindkey -r '^r'
reload-shell() {
  source ${ZDOTDIR:-$HOME}/.zshrc 
  zle reset-prompt
}
zle -N reload-shell
bindkey '^r' reload-shell

# rangerをctrl+eで起動
ranger-cd() {
  ranger --choosedir=$HOME/.rangerdir < $TTY
  LASTDIR=$(cat $HOME/.rangerdir)
  cd "$LASTDIR"
  zle reset-prompt
}
zle -N ranger-cd
bindkey '^e' ranger-cd

# fzf-tabはzeno-completionと競合するため無効化
# zsh-autocompleteと組み合わせる場合、いい感じに補完をするために以下の設定を追加
# my-fzf-tab() {
#   functions[compadd]=$functions[-ftb-compadd]
#   zle fzf-tab-complete
# }
# zle -N my-fzf-tab
# bindkey "^I" my-fzf-tab
