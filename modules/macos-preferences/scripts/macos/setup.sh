#!/bin/bash
# Authenticate once, then run package installation and settings as the current user.
set -euo pipefail

if [ "$(uname -s)" != Darwin ]; then
    echo "Not macOS!" >&2
    exit 1
fi
profile="${1:-full}"
make_bin="${2:-make}"
case "$profile" in
    core|full) ;;
    *) echo "Unknown profile: $profile (expected core or full)" >&2; exit 2 ;;
esac
if ! command -v brew >/dev/null 2>&1; then
    echo "Run make macos-init and add Homebrew to PATH first." >&2
    exit 1
fi
if [ "$(id -u)" = 0 ]; then
    echo "Run make setup as your normal user, without sudo." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${DOTFILES_REPO_ROOT:-$SCRIPT_DIR/../..}"
echo "[1/4] Administrator authentication (Homebrew runs as your normal user)"
sudo -v
# Homebrew's privilege probe resets the sudo timestamp. We have just verified it;
# tell child brew processes to reuse that check instead of revoking our credential.
export HOMEBREW_SUDO_CHECKED=1
echo "[2/4] Configure sudo Touch ID"
bash "$SCRIPT_DIR/sudo-touchid.sh"

# Refresh the existing credential only; never prompt from the background.
(
    sleeper_pid=""
    trap '[ -z "$sleeper_pid" ] || kill "$sleeper_pid" 2>/dev/null; exit 0' TERM INT
    while :; do
        sleep 30 &
        sleeper_pid=$!
        wait "$sleeper_pid" || exit
        sleeper_pid=""
        if ! sudo -n -v; then
            echo "sudo authentication expired; run sudo -v and rerun make setup if installation fails." >&2
            exit 1
        fi
    done
) &
keepalive_pid=$!
cleanup() {
    kill "$keepalive_pid" 2>/dev/null || true
    wait "$keepalive_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "[3/4] Install packages (profile: $profile; detailed Homebrew output follows)"
"$make_bin" packages PROFILE="$profile"
# Never start settings after losing authentication, nor report false completion.
if ! sudo -n -v; then
    echo "sudo authentication expired. Run sudo -v, then rerun make setup." >&2
    exit 1
fi
echo "[4/4] Apply files and app settings"
"$make_bin" apply
echo "Setup complete. macOS permission prompts and initial app sign-in may still require manual action."
