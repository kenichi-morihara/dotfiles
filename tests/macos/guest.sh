#!/bin/bash
# Run only inside a disposable macOS VM.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUTPUT="${1:?usage: guest.sh OUTPUT_DIRECTORY}"
mkdir -p "$OUTPUT"
exec > >(tee "$OUTPUT/guest.log") 2>&1
cd "$ROOT"
sw_vers
uname -m
shasum -a 256 .bin/macos/.Brewfile > "$OUTPUT/brewfile.sha256"
# Tart expands the backing disk; APFS needs to consume its new free space too.
container=$(diskutil info -plist / | plutil -extract APFSContainerReference raw -)
if ! sudo -n diskutil apfs resizeContainer "$container" 0 > "$OUTPUT/disk-resize.log" 2>&1; then
    # The guest agent may already have expanded it during boot.
    if ! grep -q 'Error: -69743:' "$OUTPUT/disk-resize.log"; then
        echo 'Could not grow the guest APFS container; see disk-resize.log' >&2
        exit 1
    fi
fi
df -h / > "$OUTPUT/disk-space.txt"
export NONINTERACTIVE=1
if ! bash .bin/macos/init.sh; then
    echo 'Bootstrap failed; complete Command Line Tools setup before retrying.'
    exit 1
fi
if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    eval "$(/usr/local/bin/brew shellenv)"
fi
brew --version
command brew list --versions > "$OUTPUT/installed-before.txt"
# The pinned CI base image includes npm-installed Yarn/pnpm. Normalize those
# before testing the manifest's Corepack implementation; this runs in the VM only.
if command -v npm >/dev/null 2>&1; then
    command npm list --global --depth=0 > "$OUTPUT/npm-before.txt" 2>&1 || true
    if ! command npm uninstall --global yarn pnpm > "$OUTPUT/npm-normalize.log" 2>&1; then
        echo 'Could not remove base-image Yarn/pnpm; see npm-normalize.log' >&2
        exit 1
    fi
fi
# Normalize the CI image's older Node before the main install.
if ! command brew install node > "$OUTPUT/node-bootstrap.log" 2>&1; then
    echo 'Node bootstrap failed; see node-bootstrap.log' >&2
    exit 1
fi
if command brew list --formula corepack >/dev/null 2>&1; then
    command brew link corepack > "$OUTPUT/corepack-link.log" 2>&1 || exit 1
fi
# Record all phase statuses; shell validation still runs after a bundle failure.
# Use the same default mode as brew.sh. Homebrew 7.0.x verbose mode skips
# its npm-specific Node PATH setup.
command brew bundle --file="$ROOT/.bin/macos/.Brewfile" > "$OUTPUT/bundle.log" 2>&1
bundle_status=$?
command brew bundle check --file="$ROOT/.bin/macos/.Brewfile" > "$OUTPUT/bundle-check.log" 2>&1
check_status=$?
python3 tests/macos/shell-smoke.py --output "$ROOT/.validation/shell"
shell_status=$?
mkdir -p "$OUTPUT/shell"
for artifact in result.json shell.log links.log; do
    if [ -f "$ROOT/.validation/shell/$artifact" ]; then
        cp "$ROOT/.validation/shell/$artifact" "$OUTPUT/shell/"
    fi
done
bash tests/macos/runtimes.sh "$ROOT/.validation/shell/home" "$OUTPUT/runtimes"
runtime_status=$?
command brew list --versions > "$OUTPUT/installed.txt"
printf '{"bundle_exit_code":%s,"bundle_check_exit_code":%s,"shell_exit_code":%s,"runtimes_exit_code":%s}\n' \
    "$bundle_status" "$check_status" "$shell_status" "$runtime_status" > "$OUTPUT/result.json"
[ "$bundle_status" -eq 0 ] && [ "$check_status" -eq 0 ] && [ "$shell_status" -eq 0 ] && [ "$runtime_status" -eq 0 ]
