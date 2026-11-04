# Dotfiles

このリポジトリは、macOS・Linux・Windows に対応したdotfilesです。

## ディレクトリ構造

```text
.chezmoiroot                 # chezmoiの管理対象をhome/に限定
home/
  .chezmoi.toml.tmpl         # checkoutの場所をchezmoiに登録
  .chezmoiignore             # OSごとの配布対象
  .chezmoiscripts/           # 初回だけ既存設定を退避
  dot_zshrc.tmpl             # 共通シェルモジュールを読み込む入口
  dot_config/                # ~/.config/ に配布する設定
    karabiner/              # macOSのみ
    hypr/, omarchy/         # Linuxのみ
    windows/                # Windowsのみ
  dot_cursor/rules/         # ~/.cursor/rules/ に配布
.bin/
  common/                   # Zshモジュール、共通セットアップ
  macos/                    # Homebrew、macOS初期化
  linux/                    # Arch Linuxパッケージ導入
  windows/                  # Windows設定適用
  link.sh                   # 旧手順互換のchezmoi移行入口
```

設定ファイルはシンボリックリンクではなくchezmoiが配布する通常ファイルです。
パッケージはHomebrew/yay、言語ランタイムはmise、設定の配布はchezmoiが担当します。

## セットアップ手順

### Makefileからの操作

リポジトリのルートで `make` を実行すると操作一覧を表示します。
macOS/LinuxではGNU Makeを使用します（macOS付属のmakeでも実行可能）。

```sh
make init             # 初回移行・設定配布・chezmoiへのcheckout登録
make diff             # 配布するファイルの差分
make dry-run          # ファイル配布のプレビュー（書き込みなし）
make apply            # ファイル配布 → アプリ設定をまとめて適用
make apply-files      # ファイル配布のみ
make apply-apps       # アプリ設定をまとめて適用（macOS）
make status           # 配布先ファイルの変更状況
make verify           # 配布先ファイルの一致確認
make test             # 既存テスト一式
```

`make apply` はファイルの競合時に停止します。Rectangleは変更前にバックアップし、
起動中なら再起動します。`diff`・`dry-run`・`status`・`verify` の対象はchezmoiの
管理ファイルで、Rectangle・Nani・iTerm2のアプリ内設定は含みません。
`make init` はファイル配布とchezmoi登録までを行い、Rectangleは `make apply` または
`make apply-apps` で適用します。

新規Macの準備は `make macos-init` → HomebrewのPATH設定 → `make packages` →
`make init` → `make apply` の順です。パッケージの既定はcoreで、全構成は
`make packages PROFILE=full`、不足確認は `make packages-check` で実行します。
ランタイム導入は `make runtimes`、ログインシェル変更は `make shell-setup` を使用します。
これらの導入・変更処理は `make apply` には含みません。

### 1. リポジトリのクローン

```bash
ghq list --full-path  # 既存checkoutがあればそれを利用
ghq get github.com/kenichi-morihara/dotfiles
cd "$(ghq root)/github.com/kenichi-morihara/dotfiles"
```

### macOS: 設定配布前の準備

新規Macでは、先にCommand Line ToolsとHomebrew、シェルの依存ツールを導入します。
会社指定のアプリと重複しないよう `.bin/macos/.Brewfile` を確認してください。

```bash
.bin/macos/init.sh
# Command Line Toolsのインストールが開始された場合は、完了後に再実行

# HomebrewのPATHを現在のシェルに反映
if [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  eval "$(/usr/local/bin/brew shellenv)"
fi

# Homebrewインストーラーの案内に従い、shellenvを ~/.zprofile にも設定
.bin/macos/brew.sh --profile core
# 個人MacなどでGUIアプリや追加の開発ツールも入れる場合
# .bin/macos/brew.sh --profile full
```

`.bin/macos/brew.sh` の既定は全構成です。`core` は対話シェルとランタイムの
起動に使うCLI一式、`full` はGUIアプリ・エディタ拡張・追加開発ツールを含む
従来の全構成です。各プロファイルの不足確認は
`.bin/macos/brew.sh --profile core check` / `.bin/macos/brew.sh check` で行えます。
その他の引数も `brew bundle` に渡します。
パッケージの宣言・オプションは `.bin/macos/.Brewfile` が正です。
`.Brewfile.core` は分類だけを持ち、全構成から該当する宣言を読み込みます。
`brew bundle dump` による全構成の自動更新後も、この分類を維持します。

### 2. chezmoiで設定を配布する

macOSではcoreプロファイルにchezmoiが含まれます。先に個別導入する場合は
`command brew install chezmoi`、Arch Linuxでは `sudo pacman -S chezmoi` を使います。
初回移行の退避処理にはPython 3も必要です（macOSのCommand Line Tools導入後に利用可能）。
旧link.sh方式を利用中の場合は `.bin/link.sh` を実行してください。先に設定を安全に移行し、
chezmoiの登録を行うので、既存の `~/.config` が外部へのリンクでもそこへ設定を書き込みません。
新規HOMEでは次の手順を使えます。

```bash
chezmoi init --source "$PWD"
chezmoi diff
chezmoi apply
```

初回の `apply` は、既存の管理対象ファイルを `.backup`、既存なら `.backup.1` 以降に
退避してから配布します。既存ディレクトリの無関係なファイルは保持し、ディレクトリの
シンボリックリンクは内容を保持して通常ディレクトリへ移行します。外部のリンク先は変更しません。
この退避処理はmacOS/Linuxで初回だけ実行され、以降はchezmoiの状態管理で再適用します。
checkoutを移動しても退避処理は再実行されません。ただし2026-11-02以前の版で初回適用した
端末では、この修正を取り込んだ後に一度だけ再実行され、配布済みファイルの `.backup` が作られます。
不要なら削除してください。
Windowsへ移行する場合は既存設定を別途バックアップしてから適用してください。

`chezmoi apply --dry-run --verbose` で書き込みせず確認できます。
通常の再適用ではローカル編集との競合をchezmoiが検出します。自動検証では
`chezmoi apply --error-on-conflict` を使うと上書きせずエラーになります。
旧手順の `.bin/link.sh` も、同じcheckoutを指定してchezmoiを初期化・適用する薄い入口として残しています。

### 設定の編集と更新

```bash
chezmoi edit ~/.config/zeno/config.yml
chezmoi diff
chezmoi apply
# 配布先を直接編集した場合は、内容を確認してソースに取り込む
chezmoi re-add ~/.config/zeno/config.yml
```

ソースを直接編集する場合は `home/dot_config/` 内を編集し、`chezmoi apply` します。
`.bin/common/` のシェルモジュールは `.zshrc` のテンプレートからcheckout内のファイルを読み込みます。
checkoutを移動した場合は、新しい場所で `chezmoi init --source "$PWD"` と `chezmoi apply` を実行します。
秘密情報・端末固有のシェル設定は、従来どおり管理対象外の `~/.zshrc.local` に置けます。

### 3. zshのセットアップ

#### 方法1: 自動スクリプトを使用（推奨）

```bash
./setup-zsh.sh
```

このスクリプトは以下を実行します：
- zshがインストールされているか確認
- `/etc/shells` にzshを追加（必要に応じて）
- `chsh` でデフォルトシェルをzshに変更

#### 方法2: 手動で設定

1. zshがインストールされているか確認：
   ```bash
   which zsh
   ```

2. インストールされていない場合：
   - macOS: `brew install zsh`
   - Linux: ディストリビューションに応じてインストール
     - Debian/Ubuntu: `sudo apt-get install zsh`
     - CentOS/RHEL: `sudo yum install zsh`
     - Arch Linux: `sudo pacman -S zsh`

3. `/etc/shells` にzshを追加（必要に応じて）：
   ```bash
   echo $(which zsh) | sudo tee -a /etc/shells
   ```

4. デフォルトシェルをzshに変更：
   ```bash
   chsh -s $(which zsh)
   ```

5. 新しいターミナルを開くか、`exec zsh` を実行

### 4. 必要なツールのインストール

macOSで上記のBrewfileから導入済みの場合、zinit・starship・miseの個別インストールは不要です。
以下は個別に導入する場合の手順です。

#### zinit（zshプラグインマネージャー）

- macOS: `brew install zinit`
- Linux: [zinit公式ドキュメント](https://github.com/zdharma-continuum/zinit)を参照

#### starship（プロンプト）

```bash
curl -sS https://starship.rs/install.sh | sh
```

#### mise（バージョンマネージャー）

```bash
curl https://mise.run | sh
```

#### その他

- zeno: zinit経由で自動インストールされます
- fzf: macOSではHomebrew、LinuxではOSのパッケージマネージャーで導入します。
  補完・検索ウィジェットはzenoを使い、zinitからfzfを重複取得しません。

グローバルのNode・Python・Go・Deno・Lua・Ruby・Corepackは
`home/dot_config/mise/config.toml` で管理します。設定配布後に `mise install` を実行します。
Corepackは現在のNode 25に対応する0.34.7を使用し、pnpm/Yarnのバージョンは
各プロジェクトの `package.json` の `packageManager` に従います。
プロジェクト固有のランタイムは、そのプロジェクトの `mise.toml` で指定します。

Ruby 2.7.2はApple Silicon Macでも `mise install` でビルドできます（数分かかります）。
rbenvの既存インストールがあるPCでは、ビルドせずに取り込むこともできます。

```sh
mise link ruby@2.7.2 "$HOME/.rbenv/versions/2.7.2"
```

Javaはグローバルには入れません。必要なプロジェクトの `mise.toml` でバージョンを指定します。
旧pyenvのPythonも `mise link` で登録できます。
Homebrewはmise本体・CLI・アプリ・依存ライブラリを担当します。
Homebrewが依存として必要とするNode/Python/LuaJITと、macOS付属の言語・Command Line Toolsは残します。
シェルではmiseをプラグインより先に有効化し、Deno/Luaの参照先を揃えます。
Arch Linuxでは [公式のdenoパッケージ](https://archlinux.org/packages/extra/x86_64/deno/) を
`.yay-packages.txt` に含めています。

Ctrl+Rでは設定ファイルとキー割り当てを再読み込みします。プラグインのロードと
starship・miseの初期化は各シェルで一度だけ行います。これらの初期化設定を編集した場合は、
新しいシェルを起動してください。
zenoはbootstrapを明示的に読み込み、初回のウィジェット利用時にDeno・ソケット・履歴を初期化します。

#### Cursor Agent CLI

Cursor本体とterminal agentを冪等に確認し、必要なら認証します。

```bash
.bin/common/setup-cursor-agent.sh
.bin/common/setup-cursor-agent.sh --login
```

認証後は任意のrepositoryで次のように利用できます。

```bash
cursor agent --workspace "$PWD" --plan "Review the current project and propose the next task"
cursor agent --workspace "$PWD" -p --trust "Run the project checks and report failures"
```

`-p`は書き込み・shell toolへアクセスできるため、信頼できるworkspaceだけで使用してください。自動実行ではまず`--plan`またはread-only promptを使い、`--force`/`--yolo`は使用しません。

## OS固有の設定

### macOS

macOS固有の設定は `.bin/macos/` と `home/dot_config/karabiner/` に配置されています：

- **brew.zsh**: Homebrewの自動Brewfile更新機能。`install` / `uninstall` / `tap` / `untap` 成功後、master/main では Brewfile のみをコミットし、upstream を fetch・merge して push します。Brewfile に差分がなくても未送信コミットを再送します。衝突時はマージを中止し、追跡ファイルに未コミット変更がある場合は自動マージをスキップします。Git のエラーは端末に表示します。
- **notify.zsh**: macOSの通知機能
- **karabiner/**: Karabiner-Elementsの設定

#### JIS／USキーボードと入力切り替え

個人Macは `QWERTY JIS`（既定）、仕事Macは `QWERTY US` を使用します。
端末ごとの選択は `chezmoi edit-config` で既存の `[data]` セクションに
`keyboardLayout = "jis"` または `keyboardLayout = "us"` を設定して保存し、
`make apply` で反映します。初回に `[data]` がなければ追加してください。
再度 `make init` してもこの選択は維持します。

| 操作 | JIS | US |
| --- | --- | --- |
| 英数入力 | 英数キー | 左Commandを単押し |
| 日本語入力（ローマ字入力） | かなキー | 右Commandを単押し |
| コピーなど | Command＋文字 | Command＋文字（単押し切り替えは発動しない） |
| Rectangleの左右半分・最大化・復元 | Caps Lock＋矢印 | Caps Lock＋矢印 |
| ディスプレイ間移動 | Caps Lock＋Shift＋左右矢印 | Caps Lock＋Shift＋左右矢印 |

Caps Lockは押しながら使うとControl＋Option＋Command、単押しすると通常のCaps Lockです。
従来のRectangleショートカットも引き続き使えます。
macOS側で日本語入力ソースを追加し、日本語の入力方法は「ローマ字入力」に設定してください。
Karabiner-Elementsのアクセシビリティ／入力監視など、求められる権限も必要です。
プロファイルは手動選択よりchezmoiの設定を正とし、再適用時に指定のQWERTYプロファイルを選択します。
既存の大西配列プロファイルは残しています。

#### Nani

アプリ本体はBrewfileのfullプロファイルに含まれます。
新規端末ではNaniを起動・ログインし、設定画面で選択テキスト翻訳のショートカットを
一度設定してから `make apply-apps` を実行してください。
アプリ設定の入口は `.bin/macos/apps.sh` に集約し、`make apply` からも実行します。
アプリの追加時はこの入口へ処理を追加し、アプリ名のMakeターゲットは増やしません。

設定の宣言は `.bin/macos/nani.json` です。現在の選択テキスト翻訳は
`Command + Shift + J`、テーマはシステム追従、送信はEnterです。
このショートカットはブラウザのダウンロード表示などと衝突する場合があります。
変更する場合はJSONの `translate-select` を編集してください（Commandは `Meta`）。

Nani 1.1.8で確認したSQLiteの `localkv` 内の設定項目だけを更新し、
認証情報・翻訳履歴・キャッシュはGitに含めません。未指定の設定項目は維持します。
変更前の設定は `~/Library/Application Support/Nani/dotfiles-backups/` に保存し、
起動中なら終了・再起動して反映します。初期設定が未完了の場合やDB形式が変わった場合は停止します。

#### iTerm2

`.bin/macos/iterm2.json` に通常用の `Dracula` と `Hotkey Window` のフォント、
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
- **defaults.sh**: システム設定（ライブ変換オフ、Dockを自動的に隠す、バッテリー残量を%表示、iTerm2の既定プロファイル）

```bash
.bin/macos/defaults.sh          # 適用（Dock・コントロールセンター・日本語入力を再起動）
.bin/macos/defaults.sh check    # 現在の値を確認（変更しない）
```

設定を追加する場合は `defaults.sh` の `SETTINGS` に1行追加します。

- **docker.sh**: Docker Desktopの割り当てメモリ（既定16GiB、`DOCKER_MEMORY_MIB`で変更可）。
  `settings-store.json` は他の設定をDocker Desktopが管理するため、chezmoiでは配布せず `jq` で `memoryMiB` だけを書き換えます（初回のみ `.bak` を作成）。

```bash
.bin/macos/docker.sh          # 適用（反映にはDocker Desktopの再起動が必要）
.bin/macos/docker.sh check    # 現在の値を確認（変更しない）
```

- **iTerm2**: `home/private_Library/private_Application Support/iTerm2/DynamicProfiles/dotfiles.json` を
  chezmoiが配布し、iTerm2が「Dracula」プロファイルとして自動で読み込みます
  （配色は [dracula/iterm](https://github.com/dracula/iterm)、フォントはHackGen Console NF）。
  プロファイルを編集する場合はこのJSONを直接編集して `chezmoi apply` します。
  iTerm2の画面上で変更した内容はJSONに保存されないため、残したい設定はJSONへ反映します。

### Linux

Linux固有の設定は `.bin/linux/` と `home/dot_config/hypr/`・`home/dot_config/omarchy/` に配置されています：

- **yay.sh**: Arch Linuxのyayパッケージマネージャー用スクリプト
- **hypr/hypridle.conf**: Omarchy の idle（スクリーンセーバー／自動ロック）を無効化
- **omarchy/hooks/post-boot.d/00-idle-off**: 起動時に screensaver / suspend トグルをオフに維持

### Windows

Windows固有の設定は `.bin/windows/` と `home/dot_config/windows/` に配置されています。

- **gamedvr.dsc.yaml**: Xbox Game Bar / Game DVR を無効化（ゲーム起動時の `ms-gamingoverlay` ダイアログ対策）
- **desired-state.json**: NVIDIA ゲーム内オーバーレイ無効化、Armoury Crate 常駐の停止
- **configure.ps1**: 上記をこのマシンへ適用する

```powershell
powershell -ExecutionPolicy Bypass -File .bin/windows/configure.ps1
```

HKCU のユーザー設定（Game DVR / NVIDIA Overlay）は管理者なしで入ります。Armoury Crate のサービス・タスク無効化と `AllowGameDVR` は管理者で再実行すると入ります。

Armoury Crate を止めると、ASUS の RGB / ファン制御 UI と ROG マウスのバッテリー常駐も止まります。BIOS のファン設定はそのままです。

## Cursor

- **User file rules**: `home/dot_cursor/rules/*.mdc` → `~/.cursor/rules/`（`alwaysApply: true` なら全チャットに載る）
- 別端末: このリポジトリを clone して `chezmoi init --source "$PWD"`、`chezmoi apply` を実行
- プロジェクト固有の置き場・テストコマンドは、各リポジトリの `.cursor/rules/` で上書き・補足する

## カスタマイズ

### 新しい設定ファイルを追加する場合

1. アプリの共通設定は `home/dot_config/` に追加し、`chezmoi diff` / `chezmoi apply` で配布します。
2. OS固有のアプリ設定は、対象ディレクトリを `home/.chezmoiignore` のOS条件に追加します。
3. 実行権限が必要なファイルは、ソース名に `executable_` を付けます。
4. シェル処理は `.bin/common/`、OS固有処理は `.bin/macos/`・`.bin/linux/` に置き、共通Zshから読み込みます。
5. Windowsのシステム設定は `home/dot_config/windows/` と `.bin/windows/configure.ps1` を更新します。

アプリ設定の変更は `chezmoi apply`、キー割り当て・端末固有シェル設定の変更はCtrl+Rで
反映します。プラグインとstarship・miseの初期化設定の変更は、新しいシェルで確認します。

## トラブルシューティング

### zshが起動しない

1. `.zshrc` が配布されているか確認：
   ```bash
   ls -la ~/.zshrc
   ```

2. `chezmoi diff ~/.zshrc` と、テンプレート内のcheckoutへの参照を確認

### zinitが読み込めない

1. zinitがインストールされているか確認
2. `.bin/common/zinit.zsh` のパス設定が正しいか確認
3. OS別のパスが適切に設定されているか確認

## テスト

GitHub Actionsの [Tests](.github/workflows/test.yml) で、push・Pull Request時に
macOSとLinuxのテストを自動実行します。手動実行（workflow_dispatch）にも対応しています。

ローカルではmacOSまたはLinuxでPython 3・Git・Zsh・Rubyを利用して実行します。

```bash
python3 -m unittest discover -s tests -v
```

一時HOMEでのchezmoi適用・再適用・既存設定の保護・編集の衝突検出・OS選択、Brewfile指定、
導入済みツールの初期化スキップを検証します。
brewの自動コミット・pushは、偽brewと一時的なローカルGitリモートで検証します。
実際のパッケージ導入やGitHubへのpushは行いません。
既存バックアップ・リンク切れの保護、不正なBrewfileプロファイルの拒否、
brew失敗時の終了コードも検証します。VMでの実導入テストは手動実行です。

新規HOMEでの初回起動時間と、同じHOMEで繰り返した起動時間は次で計測します。

```bash
python3 tests/macos/shell-benchmark.py \
  --output .validation/shell-benchmark-$(date +%Y%m%d-%H%M%S)
```

計測は一時HOME上の対話・ログインzshをPTYで起動し、最初のコマンドを受け付ける時刻と、
補完・履歴検索・zenoの準備完了時刻を別々に記録します。各シェルで5回再読み込みし、
PATH・fpath・フック・プラグイン登録・zenoサーバーが増えないことと、終了後にサーバーが
残らないことも検証します。Homebrew自体はホストと共用します。

検証環境（新規HOME・macOS VM）の作成と実行は [tests/macos/README.md](tests/macos/README.md)、実行結果は [tests/macos/VALIDATION.md](tests/macos/VALIDATION.md) を参照してください。

### 新規macOSでの最終確認

一時HOMEのテストは、現在のMacにあるツールやOS状態を完全には隔離しません。
クリーンなmacOS VMまたは新しいMacで、次を確認してください。

- 上記の準備からchezmoi適用まで順に実行できること
- `home/dot_config/mise/config.toml` の指定どおり `mise install` と `mise current` が動くこと
- 新しいターミナルでエラーなく起動し、`command -v brew starship mise deno fzf ghq` が成功すること
- 初回のプラグイン取得完了後、補完・上下キーの履歴検索・Ctrl+Gの移動・Ctrl+Rの再読込が動くこと
- 通知とKarabinerのキー操作が、macOSの必要な権限を付与した後に動くこと
- `chezmoi apply` を再実行しても設定が変わらないこと

`brew install/uninstall/tap/untap` の成功時には、対話シェルのラッパーが
Brewfileを更新し、main/masterでは自動コミットとupstreamへのpushを試行します。
実際の導入リハーサルでは `command brew ...` でラッパーを回避できます。

## ライセンス

MIT
