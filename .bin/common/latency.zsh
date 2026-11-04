# In-memory timings only: do not write paths, shell input, or history to a log.
zmodload zsh/datetime
: ${DOTFILES_LATENCY_THRESHOLD_MS:=100}
typeset -gA DOTFILES_LATENCY_MS

_dotfiles-record-latency() {
  emulate -L zsh
  local label="$1" elapsed="$2"
  local threshold="${DOTFILES_LATENCY_THRESHOLD_MS:-100}"
  [[ $threshold == <-> ]] || threshold=100
  DOTFILES_LATENCY_MS[$label]="$elapsed"
  if (( elapsed >= threshold )); then
    local message
    printf -v message '[latency] %s: %.0fms (threshold %sms)' "$label" "$elapsed" "$threshold"
    if [[ ${_DOTFILES_LATENCY_DEFER:-0} == 1 ]]; then
      _DOTFILES_LATENCY_NOTICES+=("$message")
    else
      _dotfiles-show-latency "$message"
    fi
  fi
}

_dotfiles-show-latency() {
  if zle >/dev/null 2>&1; then zle -I; fi
  print -ru2 -- "$1"
}

# Keep notifications out of fzf's alternate screen; print after the widget returns.
_dotfiles-measure-zeno-shortcuts() {
  emulate -L zsh
  (( $+functions[_dotfiles-original-zeno-dispatch] )) && return 0
  (( $+functions[zeno-lazy-widget-dispatch] )) || return 0
  autoload +X zeno-lazy-widget-dispatch 2>/dev/null || true
  functions -c zeno-lazy-widget-dispatch _dotfiles-original-zeno-dispatch
  zeno-lazy-widget-dispatch() {
    local _DOTFILES_LATENCY_DEFER=1 result=0 message
    local -a _DOTFILES_LATENCY_NOTICES=()
    _dotfiles-original-zeno-dispatch "$@" || result=$?
    for message in "${_DOTFILES_LATENCY_NOTICES[@]}"; do
      _dotfiles-show-latency "${WIDGET:-zeno}: $message"
    done
    return $result
  }
}

# Call this after the plugin bootstrap. Load the function body without running it.
_dotfiles-measure-zeno-init() {
  emulate -L zsh
  (( $+functions[_dotfiles-original-zeno-init] )) && return 0
  (( $+functions[zeno-init] )) || return 0
  autoload +X zeno-init 2>/dev/null || true
  functions -c zeno-init _dotfiles-original-zeno-init
  zeno-init() {
    if [[ ${ZENO_LOADED-} == 1 ]]; then
      _dotfiles-original-zeno-init "$@"
      return $?
    fi
    local started=$EPOCHREALTIME result=0
    _dotfiles-original-zeno-init "$@" || result=$?
    _dotfiles-record-latency zeno-init "$(( (EPOCHREALTIME - started) * 1000 ))"
    return $result
  }
}

# `dotfiles-latency probe` measures enumeration independently of human selection.
dotfiles-latency() {
  emulate -L zsh
  if [[ ${1-} == probe ]]; then
    local started=$EPOCHREALTIME result=0
    command ghq list --full-path >/dev/null || result=$?
    _dotfiles-record-latency ghq-list "$(( (EPOCHREALTIME - started) * 1000 ))"
    (( result == 0 )) || return $result
  elif (( $# > 0 )); then
    print -u2 'Usage: dotfiles-latency [probe]'
    return 2
  fi
  if (( ${#DOTFILES_LATENCY_MS} == 0 )); then
    print 'No measurements yet. Use a zeno widget, or run dotfiles-latency probe.'
    return 0
  fi
  local label
  for label in ${(ok)DOTFILES_LATENCY_MS}; do
    printf '%-16s %8.1fms\n' "$label" "${DOTFILES_LATENCY_MS[$label]}"
  done
}
