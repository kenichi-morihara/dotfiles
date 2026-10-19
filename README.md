# Dotfiles

このリポジトリは、macOS・Linux・Windows に対応したdotfilesです。

## ディレクトリ構造

```
.bin/
  common/          # 共通設定
    .zshrc         # メインのzshrc（OS判定を含む）
    zinit.zsh      # zinit設定（OS別のパスに対応）
    zeno.zsh       # zeno設定
    keybindings.zsh # キーバインド設定
  macos/           # macOS固有設定
    brew.zsh
    notify.zsh
    brew.sh
    init.sh
    .Brewfile
  linux/           # Linux固有設定
    yay.sh
    .yay-packages.txt
  windows/         # Windows固有設定
    configure.ps1  # 宣言的設定の適用

.config/
  (共通設定: ranger, zeno)
  macos/           # macOS固有
    karabiner/
  linux/           # Linux固有（必要に応じて追加）
  windows/         # Windows固有
    gamedvr.dsc.yaml
    desired-state.json

.cursor/
  rules/           # Cursor ユーザー rules（全プロジェクト共通）
    tdd.mdc        # TDD（Red-Green-Refactor）必須
```

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/kenichi-morihara/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

### macOS: リンク作成前の準備

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

### 2. シンボリックリンクの作成

```bash
.bin/link.sh
```

このスクリプトは以下を実行します：
- `.bin/common/.zshrc` を `~/.zshrc` にリンク
- `.config/` 内の共通設定をファイル単位で `~/.config/` にマージリンク
- OS固有の設定（macOSの場合は `.config/macos/`、Linuxの場合は `.config/linux/`、Windowsの場合は `.config/windows/`）を `~/.config/` にリンク
- `.cursor/rules/` を `~/.cursor/rules/` にマージリンク（Cursor 全プロジェクト共通の User file rules）

既存のファイルや異なるリンクは `.backup`（既存なら `.backup.1` 以降）へ退避します。
既存ディレクトリ内の無関係なファイルは保持します。

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
- fzf: zinit経由で自動インストールされます

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

macOS固有の設定は `.bin/macos/` と `.config/macos/` に配置されています：

- **brew.zsh**: Homebrewの自動Brewfile更新機能。`install` / `uninstall` / `tap` / `untap` 成功後、master/main では Brewfile のみをコミットし、upstream を fetch・merge して push します。Brewfile に差分がなくても未送信コミットを再送します。衝突時はマージを中止し、追跡ファイルに未コミット変更がある場合は自動マージをスキップします。Git のエラーは端末に表示します。
- **notify.zsh**: macOSの通知機能
- **karabiner/**: Karabiner-Elementsの設定

### Linux

Linux固有の設定は `.bin/linux/` と `.config/linux/` に配置されています：

- **yay.sh**: Arch Linuxのyayパッケージマネージャー用スクリプト
- **hypr/hypridle.conf**: Omarchy の idle（スクリーンセーバー／自動ロック）を無効化
- **omarchy/hooks/post-boot.d/00-idle-off**: 起動時に screensaver / suspend トグルをオフに維持

### Windows

Windows固有の設定は `.bin/windows/` と `.config/windows/` に配置されています。

- **gamedvr.dsc.yaml**: Xbox Game Bar / Game DVR を無効化（ゲーム起動時の `ms-gamingoverlay` ダイアログ対策）
- **desired-state.json**: NVIDIA ゲーム内オーバーレイ無効化、Armoury Crate 常駐の停止
- **configure.ps1**: 上記をこのマシンへ適用する

```powershell
powershell -ExecutionPolicy Bypass -File .bin/windows/configure.ps1
```

HKCU のユーザー設定（Game DVR / NVIDIA Overlay）は管理者なしで入ります。Armoury Crate のサービス・タスク無効化と `AllowGameDVR` は管理者で再実行すると入ります。

Armoury Crate を止めると、ASUS の RGB / ファン制御 UI と ROG マウスのバッテリー常駐も止まります。BIOS のファン設定はそのままです。

## Cursor

- **User file rules**: `.cursor/rules/*.mdc` → `~/.cursor/rules/`（`alwaysApply: true` なら全チャットに載る）
- 別端末: このリポジトリを clone して `.bin/link.sh` を再実行すれば入る
- プロジェクト固有の置き場・テストコマンドは、各リポジトリの `.cursor/rules/` で上書き・補足する

## カスタマイズ

### 新しい設定ファイルを追加する場合

1. **共通設定**: `.bin/common/` に追加し、`.zshrc` から読み込む
2. **macOS固有**: `.bin/macos/` に追加し、`.zshrc` のOS判定部分で読み込む
3. **Linux固有**: `.bin/linux/` に追加し、`.zshrc` のOS判定部分で読み込む
4. **Windows固有**: `.config/windows/` に宣言的設定を追加し、`.bin/windows/configure.ps1` で適用する

### 設定ファイルの更新

設定ファイルを編集した後、`.zshrc` を再読み込み：

```bash
source ~/.zshrc
```

または、Ctrl+Rでシェルをリロード（設定済みのキーバインド）

## トラブルシューティング

### zshが起動しない

1. `.zshrc` のシンボリックリンクが正しく作成されているか確認：
   ```bash
   ls -la ~/.zshrc
   ```

2. `.zshrc` のパス参照が正しいか確認

### zinitが読み込めない

1. zinitがインストールされているか確認
2. `.bin/common/zinit.zsh` のパス設定が正しいか確認
3. OS別のパスが適切に設定されているか確認

## テスト

macOSでPython 3・Git・Zshを利用して実行します。

```bash
python3 -m unittest discover -s tests -v
```

一時HOMEでのリンク作成・再実行・既存設定の保護、Brewfile指定、
導入済みツールの初期化スキップを検証します。
brewの自動コミット・pushは、偽brewと一時的なローカルGitリモートで検証します。
実際のパッケージ導入やGitHubへのpushは行いません。

新規HOMEでの初回起動時間と、同じHOMEで繰り返した起動時間は次で計測します。
初回プラグイン取得後に実行すると、キャッシュ済み起動時間を比較できます。

```bash
python3 tests/macos/shell-benchmark.py \
  --output .validation/shell-benchmark-$(date +%Y%m%d-%H%M%S)
```

計測は一時HOME上の対話・ログインzshをPTYで起動し、プロンプト表示後の最初の
コマンドを受け付けるまでを測ります。Homebrew自体はホストと共用します。

検証環境（新規HOME・macOS VM）の作成と実行は [tests/macos/README.md](tests/macos/README.md)、実行結果は [tests/macos/VALIDATION.md](tests/macos/VALIDATION.md) を参照してください。

### 新規macOSでの最終確認

一時HOMEのテストは、現在のMacにあるツールやOS状態を完全には隔離しません。
クリーンなmacOS VMまたは新しいMacで、次を確認してください。

- 上記の準備からリンク作成まで順に実行できること
- `.config/mise/config.toml` の指定どおり `mise install` と `mise current` が動くこと
- 新しいターミナルでエラーなく起動し、`command -v brew starship mise deno fzf ghq` が成功すること
- 初回のプラグイン取得完了後、補完・上下キーの履歴検索・Ctrl+Gの移動・Ctrl+Rの再読込が動くこと
- 通知とKarabinerのキー操作が、macOSの必要な権限を付与した後に動くこと
- リンク作成をもう一度実行しても設定が変わらないこと

`brew install/uninstall/tap/untap` の成功時には、対話シェルのラッパーが
Brewfileを更新し、main/masterでは自動コミットとupstreamへのpushを試行します。
実際の導入リハーサルでは `command brew ...` でラッパーを回避できます。

## ライセンス

MIT
