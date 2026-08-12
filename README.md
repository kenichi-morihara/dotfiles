# Dotfiles

このリポジトリは、macOSとLinuxの両方に対応したdotfilesです。

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

.config/
  (共通設定: ranger, zeno)
  macos/           # macOS固有
    karabiner/
  linux/           # Linux固有（必要に応じて追加）

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

### 2. シンボリックリンクの作成

```bash
.bin/link.sh
```

このスクリプトは以下を実行します：
- `.bin/common/.zshrc` を `~/.zshrc` にリンク
- `.config/` 内の共通設定を `~/.config/` にリンク
- OS固有の設定（macOSの場合は `.config/macos/`、Linuxの場合は `.config/linux/`）を `~/.config/` にリンク
- `.cursor/rules/` を `~/.cursor/rules/` にマージリンク（Cursor 全プロジェクト共通の User file rules）

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

## OS固有の設定

### macOS

macOS固有の設定は `.bin/macos/` と `.config/macos/` に配置されています：

- **brew.zsh**: Homebrewの自動Brewfile更新機能
- **notify.zsh**: macOSの通知機能
- **karabiner/**: Karabiner-Elementsの設定

### Linux

Linux固有の設定は `.bin/linux/` と `.config/linux/` に配置されています：

- **yay.sh**: Arch Linuxのyayパッケージマネージャー用スクリプト
- **hypr/hypridle.conf**: Omarchy の idle（スクリーンセーバー／自動ロック）を無効化
- **omarchy/hooks/post-boot.d/00-idle-off**: 起動時に screensaver / suspend トグルをオフに維持

## Cursor

- **User file rules**: `.cursor/rules/*.mdc` → `~/.cursor/rules/`（`alwaysApply: true` なら全チャットに載る）
- 別端末: このリポジトリを clone して `.bin/link.sh` を再実行すれば入る
- プロジェクト固有の置き場・テストコマンドは、各リポジトリの `.cursor/rules/` で上書き・補足する

## カスタマイズ

### 新しい設定ファイルを追加する場合

1. **共通設定**: `.bin/common/` に追加し、`.zshrc` から読み込む
2. **macOS固有**: `.bin/macos/` に追加し、`.zshrc` のOS判定部分で読み込む
3. **Linux固有**: `.bin/linux/` に追加し、`.zshrc` のOS判定部分で読み込む

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

## ライセンス

MIT
