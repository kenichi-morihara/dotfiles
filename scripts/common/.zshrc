#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# 設定ファイルのディレクトリパスを取得
_ZSH_CONFIG_DIR="${${(%):-%x}:A:h}"
_DOTFILES_SCRIPTS_DIR="${_ZSH_CONFIG_DIR:h}"

# === 共通設定 ===
# 履歴設定
HISTFILE="$HOME/.zsh_history"
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY          # 複数のzshセッション間で履歴を共有
setopt APPEND_HISTORY         # 履歴を追記モードで保存
# setopt HIST_IGNORE_DUPS       # 重複する履歴を無視
setopt HIST_IGNORE_SPACE      # スペースで始まるコマンドを履歴に保存しない
setopt HIST_VERIFY            # 履歴展開時にコマンドを実行せずに表示
setopt HIST_REDUCE_BLANKS     # 余分な空白を削除して履歴に保存

# Plugins use Deno/Lua during loading, before mise's first prompt hook.
if [[ ${_DOTFILES_MISE_INITIALIZED:-0} != 1 ]] && (( $+commands[mise] )); then
  eval "$(mise activate zsh)"
  eval "$(mise env -s zsh)"
  typeset -g _DOTFILES_MISE_INITIALIZED=1
fi

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
    source "$_DOTFILES_SCRIPTS_DIR/macos/notify.zsh"
    source "$_DOTFILES_SCRIPTS_DIR/macos/brew.zsh"
    source "$_DOTFILES_SCRIPTS_DIR/macos/ca-certs.zsh"
    ;;
  Linux)
    source "$_DOTFILES_SCRIPTS_DIR/linux/yay.zsh"
    # Linux特有の設定（必要に応じて追加）
    ;;
esac

# starshipの初期化
if [[ ${_DOTFILES_STARSHIP_INITIALIZED:-0} != 1 ]] && (( $+commands[starship] )); then
  eval "$(starship init zsh)"
  typeset -g _DOTFILES_STARSHIP_INITIALIZED=1
fi

# 端末固有・秘密情報（git 管理外）
if [[ -f "$HOME/.zshrc.local" ]]; then
  source "$HOME/.zshrc.local"
fi

