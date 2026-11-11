# 導入・設定の更新

コマンドはリポジトリのルートで実行します。

## 1. リポジトリのクローン

```bash
ghq list --full-path  # 既存checkoutがあればそれを利用
ghq get github.com/kenichi-morihara/dotfiles
cd "$(ghq root)/github.com/kenichi-morihara/dotfiles"
```

## macOS: 設定配布前の準備

新規Macでは、先にCommand Line ToolsとHomebrew、シェルの依存ツールを導入します。
会社指定のアプリと重複しないよう `scripts/macos/.Brewfile` を確認してください。

```bash
modules/macos-preferences/scripts/macos/init.sh
# Command Line Toolsのインストールが開始された場合は、完了後に再実行

# HomebrewのPATHを現在のシェルに反映
if [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  eval "$(/usr/local/bin/brew shellenv)"
fi

# Homebrewインストーラーの案内に従い、shellenvを ~/.zprofile にも設定
scripts/macos/brew.sh --profile core
# 個人MacなどでGUIアプリや追加の開発ツールも入れる場合
# scripts/macos/brew.sh --profile full
```

`scripts/macos/brew.sh` の既定は全構成です。`core` は対話シェルとランタイムの
起動に使うCLI一式、`full` はGUIアプリ・エディタ拡張・追加開発ツールを含む
従来の全構成です。各プロファイルの不足確認は
`scripts/macos/brew.sh --profile core check` / `scripts/macos/brew.sh check` で行えます。
その他の引数も `brew bundle` に渡します。
パッケージの宣言・オプションは `scripts/macos/.Brewfile` が正です。
`.Brewfile.core` は分類だけを持ち、全構成から該当する宣言を読み込みます。
`brew bundle dump` による全構成の自動更新後も、この分類を維持します。

## 2. chezmoiで設定を配布する

macOSではcoreプロファイルにchezmoiが含まれます。先に個別導入する場合は
`command brew install chezmoi`、Arch Linuxでは `sudo pacman -S chezmoi` を使います。
初回移行の退避処理にはPython 3も必要です（macOSのCommand Line Tools導入後に利用可能）。
旧link.sh方式を利用中の場合は `scripts/link.sh` を実行してください。先に設定を安全に移行し、
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
旧手順の `scripts/link.sh` も、同じcheckoutを指定してchezmoiを初期化・適用する薄い入口として残しています。

## 設定の編集と更新

設定の正本は modules 内で編集します。例えば zeno は modules/shell-environment/modules/shell-environment/home/dot_config/zeno/config.yml です。
ルートで make diff、make apply を実行して反映します。[モジュール構成](modules.md) に編集先と配布先を記載しています。
シェルの読み込み先は checkout 内の各モジュールです。移動後は chezmoi init --source "$PWD" と make apply で参照先を更新します。
端末固有・秘密のシェル設定は ~/.zshrc.local に置きます。

## 3. zshのセットアップ

### 方法1: 自動スクリプトを使用（推奨）

```bash
./modules/shell-environment/setup-zsh.sh
```

このスクリプトでは次を実行します。

- zshがインストールされているか確認
- `/etc/shells` にzshを追加（必要に応じて）
- `chsh` でデフォルトシェルをzshに変更

### 方法2: 手動で設定

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

## 4. 必要なツールのインストール

macOSで上記のBrewfileから導入済みの場合、zinit・starship・miseの個別インストールは不要です。
以下は個別に導入する場合の手順です。

### zinit（zshプラグインマネージャー）

- macOS: `brew install zinit`
- Linux: [zinit公式ドキュメント](https://github.com/zdharma-continuum/zinit)を参照

### starship（プロンプト）

```bash
curl -sS https://starship.rs/install.sh | sh
```

### mise（バージョンマネージャー）

```bash
curl https://mise.run | sh
```

### その他

- zeno: zinit経由で自動インストールされます
- fzf: macOSではHomebrew、LinuxではOSのパッケージマネージャーで導入します。
  補完・検索ウィジェットはzenoを使い、zinitからfzfを重複取得しません。

グローバルのNode・Python・Go・Deno・Lua・Ruby・Corepackは
`modules/runtimes/home/dot_config/mise/config.toml` で管理します。設定配布後に `mise install` を実行します。
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

### Cursor Agent CLI

Cursor本体とterminal agentを冪等に確認し、必要なら認証します。

```bash
modules/editor-configs/scripts/common/setup-cursor-agent.sh
modules/editor-configs/scripts/common/setup-cursor-agent.sh --login
```

認証後は任意のrepositoryで次のように利用できます。

```bash
cursor agent --workspace "$PWD" --plan "Review the current project and propose the next task"
cursor agent --workspace "$PWD" -p --trust "Run the project checks and report failures"
```

`-p`は書き込み・shell toolへアクセスできるため、信頼できるworkspaceだけで使用してください。自動実行ではまず`--plan`またはread-only promptを使い、`--force`/`--yolo`は使用しません。

## Linux

Linux固有の設定は `scripts/linux/` と `modules/omarchy-preferences/home/dot_config/hypr/`・`modules/omarchy-preferences/home/dot_config/omarchy/` に配置されています：

- **yay.sh**: Arch Linuxのyayパッケージマネージャー用スクリプト
- **hypr/hypridle.conf**: Omarchy の idle（スクリーンセーバー／自動ロック）を無効化
- **omarchy/hooks/post-boot.d/00-idle-off**: 起動時に screensaver / suspend トグルをオフに維持

## Windows

Windows固有の設定は `scripts/windows/` と `modules/windows-preferences/home/dot_config/windows/` に配置されています。

- **gamedvr.dsc.yaml**: Xbox Game Bar / Game DVR を無効化（ゲーム起動時の `ms-gamingoverlay` ダイアログ対策）
- **desired-state.json**: NVIDIA ゲーム内オーバーレイ無効化、Armoury Crate 常駐の停止
- **configure.ps1**: 上記をこのマシンへ適用する

```powershell
powershell -ExecutionPolicy Bypass -File modules/windows-preferences/scripts/windows/configure.ps1
```

HKCU のユーザー設定（Game DVR / NVIDIA Overlay）は管理者なしで入ります。Armoury Crate のサービス・タスク無効化と `AllowGameDVR` は管理者で再実行すると入ります。

Armoury Crate を止めると、ASUS の RGB / ファン制御 UI と ROG マウスのバッテリー常駐も止まります。BIOS のファン設定はそのままです。

## Cursor

- **User file rules**: `modules/editor-configs/home/dot_cursor/rules/*.mdc` → `~/.cursor/rules/`（`alwaysApply: true` なら全チャットに載る）
- 別端末: このリポジトリを clone して `chezmoi init --source "$PWD"`、`chezmoi apply` を実行
- プロジェクト固有の置き場・テストコマンドは、各リポジトリの `.cursor/rules/` で上書き・補足する

## カスタマイズ

### 新しい設定ファイルを追加する場合

1. アプリの共通設定は `home/dot_config/` に追加し、`chezmoi diff` / `chezmoi apply` で配布します。
2. OS固有のアプリ設定は、対象ディレクトリを `home/.chezmoiignore` のOS条件に追加します。
3. 実行権限が必要なファイルは、ソース名に `executable_` を付けます。
4. シェル処理は `scripts/common/`、OS固有処理は `scripts/macos/`・`scripts/linux/` に置き、共通Zshから読み込みます。
5. Windowsのシステム設定は `modules/windows-preferences/home/dot_config/windows/` と `modules/windows-preferences/scripts/windows/configure.ps1` を更新します。

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
2. `modules/shell-environment/scripts/common/zinit.zsh` のパス設定が正しいか確認
3. OS別のパスが適切に設定されているか確認
