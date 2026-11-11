# macOS のアプリ・システム設定

コマンドはリポジトリのルートで実行します。

macOS固有の設定は `scripts/macos/` と `home/dot_config/karabiner/` に配置されています：

- **brew.zsh**: Homebrewの自動Brewfile更新機能。`install` / `uninstall` / `tap` / `untap` 成功後、master/main では Brewfile のみをコミットし、upstream を fetch・merge して push します。Brewfile に差分がなくても未送信コミットを再送します。衝突時はマージを中止し、追跡ファイルに未コミット変更がある場合は自動マージをスキップします。Git のエラーは端末に表示します。
- **notify.zsh**: macOSの通知機能
- **karabiner/**: Karabiner-Elementsの設定

## JIS／USキーボードと入力切り替え

個人Macは `QWERTY JIS`（既定）、仕事Macは `QWERTY US` を使用します。
端末ごとの選択は `chezmoi edit-config` で既存の `[data]` セクションに
`keyboardLayout = "jis"` または `keyboardLayout = "us"` を設定して保存し、
`make apply` で反映します。初回に `[data]` がなければ追加してください。
再度 `make init` してもこの選択は維持します。

| 操作 | JIS | US |
| --- | --- | --- |
| 英数入力 | 英数キー | 元の左Commandを単押し |
| 日本語入力（ローマ字入力） | かなキー | 右Commandを単押し |
| コピーなど | Command＋文字 | Command＋文字（単押し切り替えは発動しない） |
| Rectangleの左右半分・最大化・復元 | Control＋Option＋Command＋矢印 | Control＋Option＋Command＋矢印 |
| ディスプレイ間移動 | Control＋Option＋Command＋Shift＋左右矢印 | Control＋Option＋Command＋Shift＋左右矢印 |

USではFnをControl、左ControlをOption、左OptionをCommandとして使います。
JISではCaps LockとControlはmacOS側の修飾キー設定に従います。
macOS側で日本語入力ソースを追加し、日本語の入力方法は「ローマ字入力」に設定してください。
Karabiner-Elementsのアクセシビリティ／入力監視など、求められる権限も必要です。
プロファイルは手動選択よりchezmoiの設定を正とし、再適用時に指定のQWERTYプロファイルを選択します。
既存の大西配列プロファイルは残しています。

## Nani

アプリ本体はBrewfileのfullプロファイルに含まれます。
新規端末ではNaniを起動・ログインし、設定画面で選択テキスト翻訳のショートカットを
一度設定してから `make apply-apps` を実行してください。
アプリ設定の入口は `scripts/macos/apps.sh` に集約し、`make apply` からも実行します。
アプリの追加時はこの入口へ処理を追加し、アプリ名のMakeターゲットは増やしません。

設定の宣言は `scripts/macos/nani.json` です。

- クイック翻訳（`translate-select`）は `Control + Option + J`
- アプリを開く（`translate-new`）は `Control + Command + J`

JSONではOptionを `Alt`、Commandを `Meta` と表記します。
テーマはシステム追従、送信はEnterです。

Nani 1.1.8で確認したSQLiteの `localkv` 内の設定項目だけを更新し、
認証情報・翻訳履歴・キャッシュはGitに含めません。未指定の設定項目は維持します。
変更前の設定は `~/Library/Application Support/Nani/dotfiles-backups/` に保存し、
起動中なら終了・再起動して反映します。初期設定が未完了の場合やDB形式が変わった場合は停止します。

## iTerm2

`scripts/macos/iterm2.json` に通常用の `Dracula` と `Hotkey Window` のフォント、
ホットキーウィンドウの動作を宣言しています。`make apply` / `make apply-apps` で反映します。

- フォント：`HackGen35ConsoleNFJ-Regular`、12pt（両プロファイル）
- 呼び出し：Controlを2回押す
- ホットキーウィンドウ：最前面表示、フォーカスを外すと自動で隠れる

フォントは既存Brewfileの `font-hackgen-nerd` で導入します（`make packages PROFILE=full`）。
設定変更が必要なときはiTerm2を終了し、Terminal.appなどから適用してください。
作業中のシェルは自動で終了しません。既に設定が一致している場合は起動中でも何もしません。
既存のプロファイルは名前で照合して対象項目だけを更新し、GUID・配色・コマンドなどを維持します。
新しい端末では通常用とホットキー用のプロファイルを作成し、Draculaをデフォルトにします。
配色は既存のデフォルトプロファイルから継承します（Draculaテーマの配布は含みません）。
変更前の設定は `~/Library/Application Support/iTerm2/dotfiles-backups/` に保存します。
iTerm2独自の外部設定フォルダーを利用中の場合は、二重管理を避けるため停止します。

## システム設定

`scripts/macos/defaults.sh` で Spotlight のショートカットとインデックス、キーリピート、ライブ変換、Dock、バッテリー残量の表示、iTerm2 の既定プロファイルを設定します。
キーリピートは `KeyRepeat=2`、`InitialKeyRepeat=15` です。

```bash
scripts/macos/defaults.sh          # 適用（Dock・コントロールセンター・日本語入力を再起動）
scripts/macos/defaults.sh check    # 現在の値を確認（変更しない）
```

設定を追加する場合は `defaults.sh` の `SETTINGS` に1行追加します。

## Docker Desktop

`scripts/macos/docker.sh` で Docker Desktop の割り当てメモリを設定します。既定は16GiBで、`DOCKER_MEMORY_MIB` で変更できます。
`settings-store.json` は他の設定を Docker Desktop が管理するため、`jq` で `memoryMiB` を書き換えます。初回に `.bak` を作成します。

```bash
scripts/macos/docker.sh          # 適用（反映にはDocker Desktopの再起動が必要）
scripts/macos/docker.sh check    # 現在の値を確認（変更しない）
```

## iTerm2 の Dynamic Profile

`home/private_Library/private_Application Support/iTerm2/DynamicProfiles/dotfiles.json` を
  chezmoiが配布し、iTerm2が「Dracula」プロファイルとして自動で読み込みます
  （配色は [dracula/iterm](https://github.com/dracula/iterm)、フォントはHackGen Console NF）。
  プロファイルを編集する場合はこのJSONを直接編集して `chezmoi apply` します。
  iTerm2の画面上で変更した内容はJSONに保存されないため、残したい設定はJSONへ反映します。

## 入力ソース（Google 日本語入力）

`scripts/macos/input-sources.json` にABCとひらがな（Google）、選択中の入力ソースを宣言しています。
`make apply-apps` / `make apply` でCarbonの入力ソースAPIから適用します。
宣言以外のキーボード入力ソースは無効化し、文字ビューアなどは維持します。

```bash
brew install --cask google-japanese-ime
# 初回インストール後はログアウト・再ログインしてから実行
swift scripts/macos/input-sources.swift scripts/macos/input-sources.json
swift scripts/macos/input-sources.swift scripts/macos/input-sources.json --check
```

ログイン中のMacのターミナルで実行してください。Google IMEのローマ字入力・かな入力の
設定や辞書・学習履歴はこの設定には含めません。ローマ字入力はGoogle IMEの既定値です。

## RaycastのホットキーをKarabinerで管理

Command＋Shift＋VでRaycastのClipboard Historyを開きます。
全キーボードプロファイルの `complex_modifications` に定義してあり、
`make apply-files` で配布します。RectangleはControl＋Option＋Command＋矢印で操作します。

ホットキーは `home/dot_config/karabiner/karabiner.json.tmpl` を編集します。
Raycastの各コマンドで「Copy Deeplink」して得たURLを `shell_command` の
`/usr/bin/open -g 'raycast://…'` に指定します。Raycast側で同じキーを割り当てる必要はありません。
Deeplinkの実行確認が表示された場合は、内容を確認して許可してください。

前提はKarabiner-ElementsとRaycastのインストール・起動、およびKarabinerが要求する
入力監視・ドライバなどの初回設定です。これらのmacOS側の許可はdotfilesでは復元しません。
この方法で管理するのはキー割り当てで、Raycastの拡張設定全体のexport/importではありません。

## 従来の macOS セットアップ入口

`scripts/macos/setup.sh` は sudo 認証・Touch ID 設定・パッケージ導入・設定適用をまとめる旧入口です。
`bash scripts/macos/setup.sh core` または `full` で実行します。
実行中は sudo の認証を更新し、失敗・中断時に更新処理を終了します。
パッケージ導入が失敗した場合は設定適用へ進みません。

現在の profile 対応手順は `make profile-select` → `make setup-plan` → `make setup` です。
Touch ID は `make sudo-touchid`、システム設定は `make apply-system` で個別に適用します。

## sudoをTouch IDで認証する

```sh
make sudo-touchid
```

初回だけ管理者認証が必要です。以降はTouch IDを登録したローカルのターミナルで
`sudo` の指紋認証を利用できます。
`/etc/pam.d/sudo_local` にApple標準の `pam_tid.so` を追加し、
既存のローカル設定はバックアップして保持します。パスワード認証も引き続き使えます。
SSHなど指紋認証を使えない環境では、パスワード認証になります。

確認は `sudo -k` → `sudo -v` で行えます。

## アプリ設定の再適用と確認

`make apply-apps` は未導入のアプリをスキップします。Naniは起動して初期設定が
作られるまでスキップし、DB破損などのエラーは失敗として扱います。設定が一致する
アプリは書き込み・バックアップ・再起動を行いません。失敗があっても残りを処理し、
最後に失敗した項目を表示して終了コード1を返します。

```bash
bash scripts/macos/apps.sh --check  # 書き込みなしで一致・差分・スキップを確認
```

iTerm2の設定が異なり、iTerm2が起動中の場合は自動終了せず失敗として報告します。
その場合はiTerm2を終了し、Terminal.appから再適用してください。

`scripts/macos/setup.sh` は認証・Touch ID設定・パッケージ導入・設定適用を `[1/4]`〜`[4/4]` で
表示します。Homebrewは `--verbose` で実行し、ダウンロードやインストーラーの出力も表示します。
全体の残り時間や進捗率は表示しません。

## Ghostty（通常ウィンドウ・一時ウィンドウ）

full構成に `ghostty` を含めています。設定は `home/dot_config/ghostty/config` を
chezmoiで `~/.config/ghostty/config` へ配布します（macOSのみ）。

- Control＋バッククォート（`）: 一時ウィンドウを表示・非表示
- マウスがある画面の上端に高さ60%で表示し、フォーカスを外すと隠す
- Draculaテーマ、HackGen Console NF、12pt
- 設定再読み込み: Command＋Shift＋カンマ

初回起動時にグローバルキー用のアクセシビリティ許可が必要です。
Ghosttyを起動した状態で使用します。iTerm2の設定・アプリは併存させています。
