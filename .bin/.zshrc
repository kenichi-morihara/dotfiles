#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# 設定ファイルのディレクトリパスを取得
_ZSH_CONFIG_DIR="${${(%):-%x}:A:h}"

# zinitプラグイン管理
source "$_ZSH_CONFIG_DIR/zinit.zsh"

# zeno設定
source "$_ZSH_CONFIG_DIR/zeno.zsh"

# キーバインド設定
source "$_ZSH_CONFIG_DIR/keybindings.zsh"

# notify機能
source "$_ZSH_CONFIG_DIR/notify.zsh"

# brew関数
source "$_ZSH_CONFIG_DIR/brew.zsh"

# starshipとmiseの初期化
eval "$(starship init zsh)"
eval "$(mise activate zsh)"
