#!/bin/bash
# Use Apple's sudo_local hook so the setting survives system updates.
set -euo pipefail
if [ "$(uname -s)" != Darwin ]; then
    echo "Not macOS!" >&2
    exit 1
fi
local_config=/etc/pam.d/sudo_local
if [ -f "$local_config" ] && /usr/bin/grep -Eq '^[[:space:]]*auth[[:space:]]+sufficient[[:space:]]+pam_tid\.so([[:space:]]|$)' "$local_config"; then
    echo "sudo Touch ID is already enabled."
    exit 0
fi
if ! /usr/bin/grep -Eq '^[[:space:]]*auth[[:space:]]+include[[:space:]]+sudo_local([[:space:]]|$)' /etc/pam.d/sudo; then
    echo "This macOS has no sudo_local PAM hook; no changes made." >&2
    exit 1
fi
if [ "$(id -u)" != 0 ]; then
    echo "Enabling sudo Touch ID requires administrator authentication once."
    exec sudo /bin/bash "$0"
fi
# Preserve all existing local rules. Keep password authentication in /etc/pam.d/sudo.
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
printf '%s\n' 'auth       sufficient     pam_tid.so' > "$tmp"
if [ -f "$local_config" ]; then
    cp -p "$local_config" "${local_config}.backup.$(date +%Y%m%d%H%M%S)"
    cat "$local_config" >> "$tmp"
fi
/usr/bin/install -o root -g wheel -m 0644 "$tmp" "$local_config"
echo "sudo Touch ID enabled. Test from a local terminal with: sudo -k; sudo -v"
