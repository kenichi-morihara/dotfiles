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

echo "$model | ctx ${ctx:--}/100% | 5h ${five:--}/100%${five_r:+ (reset ${five_r})} | 7d ${week:--}/100%${week_r:+ (reset ${week_r})}"
