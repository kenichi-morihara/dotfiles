#!/bin/bash
# macOSのシステム設定を適用する。何度実行しても同じ状態になる。
#   .bin/macos/defaults.sh          設定を適用し、関連プロセスを再起動
#   .bin/macos/defaults.sh check    現在の値と期待値を比較（変更しない）
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
    echo "Not macOS!" >&2
    exit 1
fi

# 形式: "currentHostなら-currentHost|ドメイン|キー|型|値|再起動するプロセス"
SETTINGS=(
    # 日本語入力のライブ変換をオフ
    "|com.apple.inputmethod.Kotoeri|JIMPrefLiveConversionKey|bool|false|JapaneseIM"
    # Dockを自動的に隠す
    "|com.apple.dock|autohide|bool|true|Dock"
    # メニューバーのバッテリー残量を常に%表示
    "-currentHost|com.apple.controlcenter|BatteryShowPercentage|bool|true|ControlCenter"
    # iTerm2の既定プロファイルをchezmoiで配布したDraculaにする（DynamicProfiles/dotfiles.json）
    "|com.googlecode.iterm2|Default Bookmark Guid|string|B8869F97-9F7A-4A40-AE09-9D8A48DB2922|iTerm2"
)

normalize() {
    case "$1" in
        1|true|TRUE|YES|yes) echo true ;;
        0|false|FALSE|NO|no) echo false ;;
        *) echo "$1" ;;
    esac
}

mode="${1:-apply}"
case "$mode" in
    apply|check) ;;
    *) echo "Usage: $0 [check]" >&2; exit 2 ;;
esac

status=0
restart=()
for entry in "${SETTINGS[@]}"; do
    IFS='|' read -r host domain key type value process <<<"$entry"
    host_args=()
    [ -n "$host" ] && host_args=("$host")
    current=$(defaults ${host_args[@]+"${host_args[@]}"} read "$domain" "$key" 2>/dev/null || echo "(unset)")
    current=$(normalize "$current")

    if [ "$current" = "$value" ]; then
        echo "✓ $domain $key = $value"
        continue
    fi

    if [ "$mode" = check ]; then
        echo "✗ $domain $key = $current (expected $value)"
        status=1
        continue
    fi

    defaults ${host_args[@]+"${host_args[@]}"} write "$domain" "$key" "-$type" "$value"
    echo "→ $domain $key: $current → $value"
    restart+=("$process")
done

if [ "${#restart[@]}" -gt 0 ]; then
    for process in $(printf '%s\n' "${restart[@]}" | sort -u); do
        # macOSが自動で再起動する。名前の完全一致で止め、無関係なプロセスに触れない。
        case "$process" in
            # 作業中のターミナルを落とさない。新しいウィンドウから反映される。
            iTerm2) echo "iTerm2: 新しいウィンドウ（またはiTerm2の再起動後）からDraculaになります。" ;;
            JapaneseIM) pkill -x JapaneseIM-RomajiTyping 2>/dev/null || true
                        pkill -x JapaneseIM-KanaTyping 2>/dev/null || true ;;
            *) pkill -x "$process" 2>/dev/null || true ;;
        esac
    done
    if printf '%s\n' "${restart[@]}" | grep -qx JapaneseIM; then
        echo "ライブ変換が切り替わらない場合は、一度ログアウトしてください。"
    fi
fi

exit "$status"
