# --- eMudhra / AAA Certificate Services ルートを信頼しないための設定 ---
# /etc/ssl/cert.pem からは当該ルートを除去済み（端末ごとの手作業。.bak 参照）。
# Node は内蔵 CA バンドルを使うため、システムの cert.pem を使うよう切り替える。
# OS 更新で cert.pem が元に戻った場合は、除去を再実施すること。
_ca_bundle="${CA_BUNDLE:-/etc/ssl/cert.pem}"  # CA_BUNDLE is for tests
if [[ -f "$_ca_bundle" ]]; then
  export SSL_CERT_FILE="${SSL_CERT_FILE:-$_ca_bundle}"
  # Claude Code のネイティブ版にも同じ CA バンドルを明示的に渡す。
  export NODE_EXTRA_CA_CERTS="${NODE_EXTRA_CA_CERTS:-$_ca_bundle}"
  # pip は certifi/システムのキーチェーンに頼らず、除去済みの cert.pem を使う。
  export PIP_CERT="${PIP_CERT:-$_ca_bundle}"
  case " ${NODE_OPTIONS:-} " in
    *" --use-openssl-ca "*) ;;
    *) export NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--use-openssl-ca" ;;
  esac
fi
unset _ca_bundle
