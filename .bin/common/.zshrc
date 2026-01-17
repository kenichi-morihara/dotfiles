#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# 設定ファイルのディレクトリパスを取得
_ZSH_CONFIG_DIR="${${(%):-%x}:A:h}"
_DOTFILES_BIN_DIR="${_ZSH_CONFIG_DIR:h}"

# === 共通設定 ===
# zinitプラグイン管理
source "$_ZSH_CONFIG_DIR/zinit.zsh"

# zeno設定
source "$_ZSH_CONFIG_DIR/zeno.zsh"

# キーバインド設定
source "$_ZSH_CONFIG_DIR/keybindings.zsh"

# === OS固有設定 ===
case "$(uname -s)" in
  Darwin)
    # macOS特有の設定
    source "$_DOTFILES_BIN_DIR/macos/notify.zsh"
    source "$_DOTFILES_BIN_DIR/macos/brew.zsh"
    ;;
  Linux)
    source "$_DOTFILES_BIN_DIR/linux/yay.zsh"
    # Linux特有の設定（必要に応じて追加）
    ;;
esac

# starshipとmiseの初期化
eval "$(starship init zsh)"
eval "$(mise activate zsh)"
