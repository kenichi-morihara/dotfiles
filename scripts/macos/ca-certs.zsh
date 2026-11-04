# --- eMudhra / AAA Certificate Services ルートを信頼しないための設定 ---
# /etc/ssl/cert.pem からは当該ルートを除去済み（端末ごとの手作業。.bak 参照）。
# Node は内蔵 CA バンドルを使うため、システムの cert.pem を使うよう切り替える。
# OS 更新で cert.pem が元に戻った場合は、除去を再実施すること。
if [[ -f /etc/ssl/cert.pem ]]; then
  export SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/ssl/cert.pem}"
  # pip は certifi/システムのキーチェーンに頼らず、除去済みの cert.pem を使う。
  export PIP_CERT="${PIP_CERT:-/etc/ssl/cert.pem}"
  case " ${NODE_OPTIONS:-} " in
    *" --use-openssl-ca "*) ;;
    *) export NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--use-openssl-ca" ;;
  esac
fi
