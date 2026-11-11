#!/bin/bash
# Claude Code status line: model | context % | 5h / 7d plan usage % (time until reset)
input=$(cat)

pct() { jq -r "$1 // empty | floor" <<<"$input" 2>/dev/null; }

# Seconds until reset; accepts epoch seconds/ms or an ISO-8601 string.
until_reset() {
  jq -r --argjson now "$(date +%s)" "$1"' // empty
    | if type == "number" then (if . > 1e12 then ./1000 else . end)
      else sub("\\.[0-9]+"; "") | sub("\\+00:?00$"; "Z") | fromdateiso8601 end
    | (. - $now) | floor | if . < 0 then 0 else . end' <<<"$input" 2>/dev/null
}

fmt() {  # 3d4h / 2h13m / 45m
  local s=$1
  [ -z "$s" ] && return
  if   (( s >= 86400 )); then printf '%dd%dh' $((s/86400)) $((s%86400/3600))
  elif (( s >= 3600  )); then printf '%dh%02dm' $((s/3600)) $((s%3600/60))
  else                        printf '%dm' $((s/60))
  fi
}

model=$(jq -r '.model.display_name // "?"' <<<"$input")
ctx=$(pct .context_window.used_percentage)
five=$(pct .rate_limits.five_hour.used_percentage)
week=$(pct .rate_limits.seven_day.used_percentage)
five_r=$(fmt "$(until_reset .rate_limits.five_hour.resets_at)")
week_r=$(fmt "$(until_reset .rate_limits.seven_day.resets_at)")

# PR for the current branch and the issues it closes ("PR #456 → #123").
# gh is slow, so the result is cached per dir+branch and refreshed in the background.
link() { printf '\e]8;;%s\a%s\e]8;;\a' "$1" "$2"; }  # OSC 8 clickable link

pr_info() {
  local dir branch cache_dir key cache
  dir=$(jq -r '.workspace.current_dir // .cwd // empty' <<<"$input")
  [ -n "$dir" ] || return
  branch=$(git -C "$dir" symbolic-ref --short HEAD 2>/dev/null) || return
  command -v gh >/dev/null || return

  cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/claude-statusline"
  mkdir -p "$cache_dir" 2>/dev/null || return
  key=$(printf '%s:%s' "$dir" "$branch" | shasum | cut -c1-16)
  cache="$cache_dir/$key"

  # Refresh when missing or older than 2 minutes; never block the status line.
  if [ -z "$(find "$cache" -mmin -2 2>/dev/null)" ]; then
    touch "$cache"  # mark as refreshing so concurrent redraws don't spawn more
    (
      cd "$dir" || exit
      json=$(gh pr view "$branch" --json number,url,closingIssuesReferences 2>/dev/null) || { : >"$cache"; exit; }
      out=$(link "$(jq -r .url <<<"$json")" "PR #$(jq -r .number <<<"$json")")
      issues=""
      while IFS=$'\t' read -r num url; do
        [ -n "$num" ] && issues+="${issues:+,}$(link "$url" "#$num")"
      done < <(jq -r '.closingIssuesReferences[]? | [.number, .url] | @tsv' <<<"$json")
      printf '%s' "$out${issues:+ → $issues}" >"$cache"
    ) >/dev/null 2>&1 &
  fi
  cat "$cache" 2>/dev/null
}

pr=$(pr_info)

echo "$model | ctx ${ctx:--}/100% | 5h ${five:--}/100%${five_r:+ (reset ${five_r})} | 7d ${week:--}/100%${week_r:+ (reset ${week_r})}${pr:+ | $pr}"
