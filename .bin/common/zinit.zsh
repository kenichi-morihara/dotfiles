# ============================================
# zinit プラグイン管理
# ============================================
# OS別のzinitパスを設定
case "$(uname -s)" in
  Darwin)
    # macOS: Homebrewでインストールした場合
    if [[ -f /opt/homebrew/opt/zinit/zinit.zsh ]]; then
      source /opt/homebrew/opt/zinit/zinit.zsh
    elif [[ -f /usr/local/opt/zinit/zinit.zsh ]]; then
      source /usr/local/opt/zinit/zinit.zsh
    fi
    ;;
  Linux)
    # Linux: 標準的なインストールパス
    if [[ -f ~/.local/share/zinit/zinit.git/zinit.zsh ]]; then
      source ~/.local/share/zinit/zinit.git/zinit.zsh
    elif [[ -f ~/.zinit/bin/zinit.zsh ]]; then
      source ~/.zinit/bin/zinit.zsh
    fi
    ;;
esac

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

# fzfのデフォルトオプション（中央表示、ボーダー、レイアウト）
export FZF_DEFAULT_OPTS='--height 80% --border --layout=reverse --info=inline'

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
