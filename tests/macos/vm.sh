#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/tests/macos/vm.env"
if [ "${1:-}" = --help ]; then
    echo 'usage: bash tests/macos/vm.sh [OUTPUT_DIRECTORY]'
    echo 'Configuration: tests/macos/vm.env; see tests/macos/README.md'
    exit 0
fi
for dependency in "$TART_BIN" python3 ssh; do
    command -v "$dependency" >/dev/null || { echo "Missing dependency: $dependency" >&2; exit 1; }
done
OUTPUT="${1:-$ROOT/.validation/$MACOS_VM_NAME}"
mkdir -p "$OUTPUT"
OUTPUT="$(cd "$OUTPUT" && pwd)"
export TART_NO_AUTO_PRUNE=1
"$TART_BIN" --version > "$OUTPUT/tart-version.txt"
printf '%s\n' "$MACOS_VM_IMAGE" > "$OUTPUT/image.txt"
printf '%s\n' "$MACOS_VM_NAME" > "$OUTPUT/vm-name.txt"
# Existing VMs are never overwritten. Supply an already-cloned, unused VM to
# skip the download with MACOS_VM_PRECLONED=1.
if [ "${MACOS_VM_PRECLONED:-0}" != 1 ]; then
    "$TART_BIN" clone "$MACOS_VM_IMAGE" "$MACOS_VM_NAME" > "$OUTPUT/clone.log" 2>&1
fi
"$TART_BIN" set "$MACOS_VM_NAME" --cpu "$MACOS_VM_CPUS" --memory "$MACOS_VM_MEMORY_MB" --disk-size "$MACOS_VM_DISK_GB"
printf 'cpu=%s\nmemory_mb=%s\ndisk_gb=%s\n' "$MACOS_VM_CPUS" "$MACOS_VM_MEMORY_MB" "$MACOS_VM_DISK_GB" > "$OUTPUT/resources.txt"
SNAPSHOT=$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-vm-source.XXXXXX")
vm_pid=""
cleanup() {
    if [ -n "$vm_pid" ]; then
        "$TART_BIN" stop "$MACOS_VM_NAME" >/dev/null 2>&1 || true
        wait "$vm_pid" 2>/dev/null || true
    fi
    rm -f "$OUTPUT/askpass.sh"
    rm -rf "$SNAPSHOT"
}
trap cleanup EXIT
# Include tracked working-tree contents and the test harness; exclude Git
# credentials, local secrets and untracked personal config files.
python3 - "$ROOT" "$SNAPSHOT" <<'PY'
from pathlib import Path
import shutil
import subprocess
import sys
root, target = map(Path, sys.argv[1:])
files = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).split(b'\0')
paths = {root / f.decode() for f in files if f}
paths.update(p for p in (root / 'tests').rglob('*') if p.is_file())
for path in paths:
    rel = path.relative_to(root)
    if '__pycache__' in rel.parts or not path.is_file():
        continue
    dst = target / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
PY
"$TART_BIN" run --no-graphics --no-audio --no-clipboard \
    --dir="repo:$SNAPSHOT:ro" --dir="results:$OUTPUT" "$MACOS_VM_NAME" > "$OUTPUT/vm.log" 2>&1 &
vm_pid=$!
# Public default credentials of the Cirrus Labs disposable base VM.
cat > "$OUTPUT/askpass.sh" <<'ASKPASS'
#!/bin/sh
printf '%s\n' admin
ASKPASS
chmod 700 "$OUTPUT/askpass.sh"
export SSH_ASKPASS="$OUTPUT/askpass.sh" SSH_ASKPASS_REQUIRE=force DISPLAY=:0
ip=""
for attempt in {1..90}; do
    if ! kill -0 "$vm_pid" 2>/dev/null; then
        cat "$OUTPUT/vm.log" >&2
        exit 1
    fi
    ip=$("$TART_BIN" ip "$MACOS_VM_NAME" 2>/dev/null || true)
    if [ -n "$ip" ] && ssh -T -o ConnectTimeout=3 -o StrictHostKeyChecking=accept-new \
        -o "UserKnownHostsFile=$OUTPUT/known_hosts" "admin@$ip" true 2>/dev/null; then
        break
    fi
    sleep 2
done
[ -n "$ip" ] || { echo 'VM did not acquire an IP address' >&2; exit 1; }
ssh -T -o ServerAliveInterval=10 -o ServerAliveCountMax=3 -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new \
    -o "UserKnownHostsFile=$OUTPUT/known_hosts" "admin@$ip" \
    'workspace=$(mktemp -d "$HOME/dotfiles-validation.XXXXXX") && cp -R "/Volumes/My Shared Files/repo" "$workspace/repo" && bash "$workspace/repo/tests/macos/guest.sh" "/Volumes/My Shared Files/results"' \
    > "$OUTPUT/ssh.log" 2>&1
