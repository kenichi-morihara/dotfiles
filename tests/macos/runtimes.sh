#!/bin/bash
# Install configured runtimes inside the HOME created by shell-smoke.py.
set -euo pipefail
runtime_home="${1:?usage: runtimes.sh FRESH_HOME OUTPUT_DIRECTORY}"
output="${2:?usage: runtimes.sh FRESH_HOME OUTPUT_DIRECTORY}"
runtime_home="$(cd "$runtime_home" && pwd)"
mkdir -p "$output"
output="$(cd "$output" && pwd)"
if [ -x /opt/homebrew/bin/mise ]; then
    mise_bin=/opt/homebrew/bin/mise
else
    mise_bin=/usr/local/bin/mise
fi
[ -f "$runtime_home/.config/mise/config.toml" ] || { echo 'Missing chezmoi-deployed mise config' >&2; exit 1; }
cd "$runtime_home"
run_mise() {
    env -i HOME="$runtime_home" PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
        XDG_CONFIG_HOME="$runtime_home/.config" XDG_DATA_HOME="$runtime_home/.local/share" \
        XDG_CACHE_HOME="$runtime_home/.cache" MISE_YES=1 "$mise_bin" "$@"
}
run_mise install > "$output/install.log" 2>&1
run_mise current > "$output/current.txt" 2>&1
run_mise exec -- /bin/sh -c 'command -v deno' > "$output/deno-source.txt"
case "$(cat "$output/deno-source.txt")" in
    /opt/homebrew/bin/deno|/usr/local/bin/deno) ;;
    *) echo 'Deno must come from Homebrew, not a global mise installation' >&2; exit 1 ;;
esac
{
    run_mise exec -- node --version
    run_mise exec -- python --version
    run_mise exec -- deno --version
} > "$output/versions.txt" 2>&1
