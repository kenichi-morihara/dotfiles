#!/bin/bash
# Check that distrusted CA roots (eMudhra emSign ECC G3 / AAA Certificate Services) stay distrusted.
#   doctor.sh            offline: bundle contents and shell environment
#   doctor.sh --online   also connect to the eMudhra test hosts with each client
# Exit status is non-zero when any check fails.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
bundle="${CA_BUNDLE:-/etc/ssl/cert.pem}"
hosts=(dv-g3b-emudhra dv-g3b-aaa-emudhra)
fail=0
ok()  { echo "OK: $*"; }
ng()  { echo "NG: $*"; fail=1; }
unk() { echo "??: $*"; }

# 1. The bundle itself.
if CA_BUNDLE="$bundle" bash "$SCRIPT_DIR/ca-certs.sh" check >/dev/null 2>&1; then
    ok "target roots are not in $bundle"
else
    ng "target roots remain in, or cannot read, $bundle -> run: make ca-certs"
fi

# 2. The environment a fresh interactive zsh would get from ca-certs.zsh.
env_out=$(env -u SSL_CERT_FILE -u PIP_CERT -u NODE_OPTIONS -u NODE_EXTRA_CA_CERTS CA_BUNDLE="$bundle" \
    zsh -c 'source "$1"; print -r -- "$SSL_CERT_FILE|$PIP_CERT|$NODE_OPTIONS|$NODE_EXTRA_CA_CERTS"' _ "$SCRIPT_DIR/ca-certs.zsh" 2>/dev/null)
IFS='|' read -r ssl pip node extra <<<"$env_out"
[ "$ssl" = "$bundle" ] && ok "SSL_CERT_FILE=$ssl" || ng "SSL_CERT_FILE is not $bundle (is $SCRIPT_DIR/ca-certs.zsh sourced from .zshrc?)"
[ "$pip" = "$bundle" ] && ok "PIP_CERT=$pip"      || ng "PIP_CERT is not $bundle"
case " $node " in *" --use-openssl-ca "*) ok "NODE_OPTIONS has --use-openssl-ca" ;; *) ng "NODE_OPTIONS lacks --use-openssl-ca (Node would use its built-in roots)" ;; esac

[ "$extra" = "$bundle" ] && ok "NODE_EXTRA_CA_CERTS=$extra" || ng "NODE_EXTRA_CA_CERTS is not $bundle"

# 3. Live probes: every client must reject both hosts. Only a certificate error counts as OK.
if [ "${1:-}" = "--online" ]; then
    probe() { # name host cmd... ; cmd prints one of: trusted | rejected | unknown
        local name=$1 host=$2; shift 2
        case "$("$@" 2>/dev/null)" in
            rejected) ok "$name rejects $host" ;;
            trusted)  ng "$name TRUSTS $host" ;;
            *)        unk "$name: cannot decide for $host (network?)" ;;
        esac
    }
    for h in "${hosts[@]}"; do
        u="$h.we-have-a-problem.com"
        curl_rc() { curl -s -o /dev/null --max-time 15 "https://$u/"; rc=$?
                    case $rc in 0) echo trusted ;; 35|60) echo rejected ;; esac; }
        probe "curl (system)" "$u" curl_rc
        if command -v node >/dev/null 2>&1; then
            node_probe() { NODE_OPTIONS="${node:-}" SSL_CERT_FILE="$bundle" NODE_USE_ENV_PROXY=1 node -e "
                require('https').get('https://$u/',r=>{console.log('trusted');r.resume()})
                .on('error',e=>console.log(/CERT|ISSUER|SELF_SIGNED/.test(e.code)?'rejected':'unknown'))"; }
            probe "node" "$u" node_probe
        fi
        if [ -x /usr/bin/python3 ]; then
            py_probe() { SSL_CERT_FILE="$bundle" /usr/bin/python3 -c "
import urllib.request,ssl
try: urllib.request.urlopen('https://$u/',timeout=15); print('trusted')
except Exception as e: print('rejected' if isinstance(getattr(e,'reason',e),ssl.SSLCertVerificationError) else 'unknown')"; }
            probe "python3 (system)" "$u" py_probe
        fi
    done
fi

[ "$fail" = 0 ] && echo "doctor: all checks passed" || echo "doctor: problems found (see NG above)"
exit "$fail"
