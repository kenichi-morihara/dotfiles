# Force ANSI colors even though fzf previews are pipes, not terminals.
if (( $+commands[bat] )); then
  export ZENO_GIT_CAT="bat --color=always --paging=never --style=plain --theme=Dracula"
else
  export ZENO_GIT_CAT="cat"
fi
if (( $+commands[eza] )); then
  export ZENO_GIT_TREE="eza --tree --level=2 --color=always"
else
  export ZENO_GIT_TREE="ls -la"
fi

# Recent zeno versions register widgets before lazy heavy initialization.
if [[ -n $ZENO_LOADED || -n $ZENO_BOOTSTRAPPED ]]; then
  source "${${(%):-%x}:A:h}/latency.zsh"
  _dotfiles-measure-zeno-init
  _dotfiles-measure-zeno-shortcuts
  # Initialize Deno/socket/history only when a bound widget is first used.
  if (( $+functions[zeno-register-lazy-widgets] )); then
    zeno-register-lazy-widgets zeno-auto-snippet zeno-ghq-cd zeno-completion \
      zeno-insert-snippet zeno-insert-space zeno-toggle-auto-snippet \
      zeno-preprompt zeno-preprompt-snippet zeno-history-selection
  fi
  bindkey ' '  zeno-auto-snippet

  # fallback if snippet not matched (default: self-insert)
  # export ZENO_AUTO_SNIPPET_FALLBACK=self-insert

  # if you use zsh's incremental search
  # bindkey -M isearch ' ' self-insert

  # bindkey '^m' zeno-auto-snippet-and-accept-line

  # Upstream ghq preview hardcodes cat; use a local widget without patching the plugin.
  typeset -g _DOTFILES_ZENO_PREVIEW="${${(%):-%x}:A:h}/zeno-project-preview.sh"
  dotfiles-zeno-ghq-cd() {
    emulate -L zsh
    local dir preview="bash ${(q)_DOTFILES_ZENO_PREVIEW} {}"
    local picker=${ZENO_FZF_COMMAND:-fzf}
    local -a picker_options
    if [[ $picker == fzf-tmux ]]; then
      if [[ -n $TMUX ]] && (( $+commands[fzf-tmux] )); then
        picker_options=(${(z)ZENO_FZF_TMUX_OPTIONS})
      else
        picker=fzf
      fi
    fi
    dir=$(ghq list --full-path | "$picker" "${picker_options[@]}" --ansi --no-multi \
      --prompt='Project >' --preview="$preview" \
      --bind='ctrl-d:preview-page-down,ctrl-u:preview-page-up')
    if [[ -z $dir ]]; then
      zle reset-prompt
      return 1
    fi
    BUFFER="cd ${(q)dir}"
    zle reset-prompt
    zle accept-line
    if (( $+widgets[zeno-ghq-cd-post-hook] )); then
      ZENO_GHQ_CD_DIR="$dir" zle zeno-ghq-cd-post-hook
    fi
  }
  zle -N dotfiles-zeno-ghq-cd
  bindkey '^g' dotfiles-zeno-ghq-cd
  # Ctrl+Shift+G: ghqでcdしてcursorで開く（fzf使用）
  ghq-cd-cursor() {
    local selected_dir
    selected_dir=$(ghq list --full-path | fzf)
    if [ -n "$selected_dir" ]; then
      cd "$selected_dir"
      cursor .
      zle reset-prompt
    fi
  }
  zle -N ghq-cd-cursor
  # bindkey '^G' ghq-cd-cursor  # Ctrl+Shift+G (Escape + G)
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

  bindkey '^h' zeno-history-selection         # classic history widget
  # bindkey '^r' zeno-smart-history-selection # smart history widget

  # fallback if completion not matched
  # (default: fzf-compdletion if exists; otherwise expand-or-complete)
  # export ZENO_COMPLETION_FALLBACK=expand-or-complete
fi
