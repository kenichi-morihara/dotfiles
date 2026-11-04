#!/bin/bash
# macOSのシステム設定を適用する。何度実行しても同じ状態になる。
#   scripts/macos/defaults.sh          設定を適用し、関連プロセスを再起動
#   scripts/macos/defaults.sh check    現在の値と期待値を比較（変更しない）
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
    echo "Not macOS!" >&2
    exit 1
fi

# 形式: "currentHostなら-currentHost|ドメイン|キー|型|値|再起動するプロセス"
SETTINGS=(
    # キーリピートを速め、長押しからの開始待ちも短めにする（ログインし直して反映）
    "|NSGlobalDomain|KeyRepeat|int|2|"
    "|NSGlobalDomain|InitialKeyRepeat|int|15|"
    # 日本語入力のライブ変換をオフ
    "|com.apple.inputmethod.Kotoeri|JIMPrefLiveConversionKey|bool|false|JapaneseIM"
    # Dockに固定するアプリを空にする（起動中のアプリは表示される）
    "|com.apple.dock|persistent-apps|array|()|Dock"
    # Dockを自動的に隠す
    "|com.apple.dock|autohide|bool|true|Dock"
    # Dockを最小限に: 表示/非表示の遅延とアニメーションなし、アイコン48px、最近使ったアプリ非表示
    "|com.apple.dock|autohide-delay|float|0|Dock"
    "|com.apple.dock|autohide-time-modifier|float|0|Dock"
    "|com.apple.dock|tilesize|int|48|Dock"
    "|com.apple.dock|magnification|bool|false|Dock"
    "|com.apple.dock|show-recents|bool|false|Dock"
    "|com.apple.dock|launchanim|bool|false|Dock"
    "|com.apple.dock|mineffect|string|scale|Dock"
    "|com.apple.dock|minimize-to-application|bool|true|Dock"
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
    if [ "$type" = array ]; then
        current=$(printf '%s' "$current" | tr -d '[:space:]')
    fi
    current=$(normalize "$current")
    expected=$(normalize "$value")

    if [ "$current" = "$expected" ]; then
        echo "✓ $domain $key = $value"
        continue
    fi

    if [ "$mode" = check ]; then
        echo "✗ $domain $key = $current (expected $expected)"
        status=1
        continue
    fi

    if [ "$type" = array ] && [ "$value" = '()' ]; then
        defaults ${host_args[@]+"${host_args[@]}"} write "$domain" "$key" -array
    else
        defaults ${host_args[@]+"${host_args[@]}"} write "$domain" "$key" "-$type" "$value"
    fi
    echo "→ $domain $key: $current → $value"
    [ -z "$process" ] || restart+=("$process")
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

# 電源設定（pmset、要sudo）。電源接続時はスリープ・画面オフなし、バッテリー時は5分（0 = 無効）。減光は無効。
# 形式: "セクション名|pmsetのフラグ|キー 値"
PMSET=(
    "AC Power|-c|sleep 0"
    "AC Power|-c|displaysleep 0"
    "Battery Power|-b|sleep 5"
    "Battery Power|-b|displaysleep 5"
    "Battery Power|-b|lessbright 0"
)
pmset_all=$(pmset -g custom)
for entry in "${PMSET[@]}"; do
    IFS='|' read -r section flag kv <<<"$entry"
    read -r key value <<<"$kv"
    current=$(awk -v s="$section:" -v k="$key" '/^[^ ]/{f=($0==s)} f && $1==k{print $2}' <<<"$pmset_all")
    current="${current:-(unset)}"

    if [ "$current" = "$value" ]; then
        echo "✓ pmset($flag) $key = $value"
    elif [ "$mode" = check ]; then
        echo "✗ pmset($flag) $key = $current (expected $value)"
        status=1
    elif sudo pmset "$flag" "$key" "$value"; then
        echo "→ pmset($flag) $key: $current → $value"
    else
        echo "✗ pmset($flag) $key: sudoに失敗しました" >&2
        status=1
    fi
done

exit "$status"
