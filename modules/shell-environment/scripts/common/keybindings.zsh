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

# Alacrittyの透過度をトグル
# 透過度の状態を保持する変数（デフォルトは1.0）
typeset -g _ALACRITTY_OPACITY=${_ALACRITTY_OPACITY:-1.0}

toggle-alacritty-opacity() {
  # 透過度を0.9と1.0でトグル（文字列比較で確実に）
  if [[ "$_ALACRITTY_OPACITY" == "1.0" ]]; then
    _ALACRITTY_OPACITY=0.6
  else
    _ALACRITTY_OPACITY=1.0
  fi

  # Alacrittyの透過度を変更
  alacritty msg config "window.opacity=$_ALACRITTY_OPACITY" 2>/dev/null

  zle reset-prompt
}
zle -N toggle-alacritty-opacity
# Alt+Oで透過度をトグル
bindkey '\eo' toggle-alacritty-opacity  # Alt+O

# fzf-tabはzeno-completionと競合するため無効化
# zsh-autocompleteと組み合わせる場合、いい感じに補完をするために以下の設定を追加
# my-fzf-tab() {
#   functions[compadd]=$functions[-ftb-compadd]
#   zle fzf-tab-complete
# }
# zle -N my-fzf-tab
# bindkey "^I" my-fzf-tab
