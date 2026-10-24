# Source only after deferred plugins have finished loading in the PTY harness.
() {
  local before_path="${(j:|:)path}" before_fpath="${(j:|:)fpath}"
  local before_hooks before_plugins before_pid="$ZENO_PID" i
  before_hooks=$(typeset -p precmd_functions preexec_functions chpwd_functions zshexit_functions 2>/dev/null)
  before_plugins="${(j:|:)ZINIT_REGISTERED_PLUGINS}"
  for i in {1..5}; do
    source "${ZDOTDIR:-$HOME}/.zshrc"
  done
  local after_hooks=$(typeset -p precmd_functions preexec_functions chpwd_functions zshexit_functions 2>/dev/null)
  local check
  for check in path fpath hooks plugins server; do
    local ok=0
    case "$check" in
      path) [[ "$before_path" == "${(j:|:)path}" ]] && ok=1 ;;
      fpath) [[ "$before_fpath" == "${(j:|:)fpath}" ]] && ok=1 ;;
      hooks) [[ "$before_hooks" == "$after_hooks" ]] && ok=1 ;;
      plugins) [[ "$before_plugins" == "${(j:|:)ZINIT_REGISTERED_PLUGINS}" ]] && ok=1 ;;
      server) [[ -n "$before_pid" && "$before_pid" == "$ZENO_PID" ]] && kill -0 "$ZENO_PID" 2>/dev/null && ok=1 ;;
    esac
    if (( ok )); then print "__CHECK_reload-${check}=PASS"; else print "__CHECK_reload-${check}=FAIL"; fi
  done
  if [[ $(bindkey '^i') == *' zeno-completion' && $(bindkey '^r') == *' reload-shell' ]]; then
    print __CHECK_reload-bindings=PASS
  else
    print __CHECK_reload-bindings=FAIL
  fi
}
