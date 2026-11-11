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
    # Spotlightの候補送信（Siriの提案・検索クエリ共有）をオフ
    "|com.apple.lookup.shared|LookupSuggestionsDisabled|bool|true|"
    "|com.apple.assistant.support|Search Queries Data Sharing Status|int|2|"
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

# Spotlightを無効にする（Command+SpaceをGhosttyのクイックターミナルに譲る）。
# ショートカットは symbolichotkeys の 64（Spotlight検索）と 65（Finder検索）を無効にする。
# 反映にはログインし直すか、activateSettings の実行が必要。
for id in 64 65; do
    current=$(/usr/libexec/PlistBuddy -c "Print :AppleSymbolicHotKeys:$id:enabled" \
        "$HOME/Library/Preferences/com.apple.symbolichotkeys.plist" 2>/dev/null || echo "(unset)")
    if [ "$current" = false ]; then
        echo "✓ symbolichotkeys $id enabled = false"
    elif [ "$mode" = check ]; then
        echo "✗ symbolichotkeys $id enabled = $current (expected false)"
        status=1
    else
        if [ "$id" = 64 ]; then params='<integer>32</integer><integer>49</integer><integer>1048576</integer>'
        else params='<integer>32</integer><integer>49</integer><integer>1572864</integer>'; fi
        defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add "$id" \
            "<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array>$params</array><key>type</key><string>standard</string></dict><key>type</key><string>standard</string></dict>"
        echo "→ symbolichotkeys $id enabled: $current → false"
        /System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u 2>/dev/null || true
    fi
done

# Spotlightのインデックス作成を全ボリュームで停止する（mdutil、要sudo）。既存インデックスは削除する。
# mdutilは無効化済みでも "Indexing disabled." を返すため、状態の文字列で判定する。
index_out=$(mdutil -a -s 2>/dev/null || true)
index_state=$(grep -c 'Indexing enabled' <<<"$index_out" || true)
if [ -z "$index_out" ]; then
    echo "✗ mdutil: 状態を取得できません（サンドボックス内では空になります）" >&2
    status=1
elif [ "$index_state" = 0 ]; then
    echo "✓ mdutil indexing = disabled"
elif [ "$mode" = check ]; then
    echo "✗ mdutil indexing enabled on $index_state volume(s) (expected disabled)"
    status=1
elif sudo mdutil -a -i off >/dev/null && sudo mdutil -a -E >/dev/null 2>&1; then
    echo "→ mdutil indexing: enabled → disabled"
else
    echo "✗ mdutil: sudoに失敗しました" >&2
    status=1
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
