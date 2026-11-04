#!/bin/bash
# Remove distrusted roots (eMudhra emSign ECC G3 / AAA Certificate Services) from /etc/ssl/cert.pem.
# macOS updates restore the file, so rerun this after OS updates. Idempotent.
#   ca-certs.sh          apply (administrator authentication once)
#   ca-certs.sh check    report only; exit 1 if a target root is still present
set -euo pipefail
if [ "$(uname -s)" != Darwin ]; then
    echo "Not macOS!" >&2
    exit 1
fi
bundle=/etc/ssl/cert.pem
# Matches the "=== /.../CN=<name>" header line of each certificate block.
pattern='^=== .*/CN=(AAA Certificate Services|emSign ECC Root CA - G3)$'

present() { /usr/bin/grep -Eq "$pattern" "$bundle"; }

case "${1:-apply}" in
    check)
        if present; then
            echo "NG: target roots are still in $bundle (run: scripts/macos/ca-certs.sh)"
            exit 1
        fi
        echo "OK: target roots are not in $bundle"
        exit 0
        ;;
    apply) ;;
    *) echo "Usage: $0 [apply|check]" >&2; exit 2 ;;
esac

if ! present; then
    echo "Target roots are already removed from $bundle."
    exit 0
fi
if [ "$(id -u)" != 0 ]; then
    echo "Editing $bundle requires administrator authentication once."
    exec sudo /bin/bash "$0" apply
fi

# Keep the first (pristine) copy; never overwrite it with an already-edited file.
[ -e "${bundle}.bak" ] || cp -p "$bundle" "${bundle}.bak"
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
before=$(/usr/bin/grep -c 'BEGIN CERTIFICATE' "$bundle")
/usr/bin/awk -v pat="$pattern" '
    /^(###|===) / { skip = 0 }
    $0 ~ pat      { skip = 1 }
    !skip
' "$bundle" > "$tmp"
if /usr/bin/grep -Eq "$pattern" "$tmp"; then
    echo "Failed to remove target roots; $bundle left unchanged." >&2
    exit 1
fi
after=$(/usr/bin/grep -c 'BEGIN CERTIFICATE' "$tmp")
/usr/bin/install -o root -g wheel -m 0644 "$tmp" "$bundle"
echo "Removed $((before - after)) root(s) from $bundle (backup: ${bundle}.bak)."
