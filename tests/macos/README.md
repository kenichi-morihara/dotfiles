# macOS導入リハーサル

今回の実行結果は [VALIDATION.md](VALIDATION.md) を参照してください。

## 初回シェルだけ確認する

Python 3、Git、Brewfileのシェル依存ツールを導入したmacOSで実行します。

```bash
python3 tests/macos/shell-smoke.py --output .validation/shell-$(date +%Y%m%d-%H%M%S)
```

新規HOME、空のユーザー設定・プラグインキャッシュ、最小限の環境変数で
実際の `/bin/zsh -il` をPTYから操作します。HomebrewのPATHは新しい `.zprofile`
で設定します。プラグインは実際にネットワークから取得し、遅延ロードを待って
コマンド9種・ウィジェット5種・zenoの準備状態・キー割り当て3種を確認します。
同じHOMEの再利用は拒否します。親シェルの `ZENO_LOADED` やPATHは引き継ぎません。

結果は指定先の `result.json`、`shell.log`、`links.log` に保存します。
Homebrew・macOS本体はホストと共用するため、新規Mac全体の検証にはVMを使います。
キーの割り当ては検証しますが、対話型の候補選択や通知・GUI権限までは検証しません。

## macOS VMで全パッケージを導入する

Apple SiliconのMacとTartを使います。Tartの導入とイメージの前提は
[公式Quick Start](https://tart.run/quick-start/)を参照してください。
初回は約26GBの圧縮イメージと、展開後のVM・全パッケージ分の空き容量が必要です。

```bash
# Tart 2.41.1をSHA-256検証付きで .validation/tools/ に展開（sudo不要）
export TART_BIN="$(bash tests/macos/bootstrap-tart.sh)"
bash tests/macos/vm.sh
```

既にTartをインストールしている場合は `TART_BIN` の指定を省略できます。

tapの定義がHomebrewに対応していない場合は、公式Quick Startの手動インストールを
使用してバイナリの場所を指定できます。

```bash
TART_BIN=/path/to/tart.app/Contents/MacOS/tart bash tests/macos/vm.sh
```

`vm.env` にデフォルトのVMイメージをdigestで固定しています。
VMは4 CPU・8GB RAM・120GBの論理ディスクで実行します
（`MACOS_VM_CPUS`・`MACOS_VM_MEMORY_MB`・`MACOS_VM_DISK_GB` で変更可能）。
ディスクはsparse形式ですが、実際の導入量に応じてホストの空き容量を使います。
同じイメージを固定して再実行する場合は、OCI digestを指定してください。
`latest` とBrewfileの未固定パッケージは実行時点の最新版になるため、
過去と完全に同じバージョン構成になることは保証しません。

```bash
MACOS_VM_IMAGE=ghcr.io/cirruslabs/macos-tahoe-base@sha256:YOUR_DIGEST \
  MACOS_VM_NAME=dotfiles-rehearsal \
  bash tests/macos/vm.sh .validation/rehearsal
```

ホスト上で実行するのはTartとSSHだけです。パッケージ導入はVM内で行います。
作業ツリーの追跡済みファイルと `tests/` をスナップショットとしてコピーするため、
未コミットの修正も検証対象です。ホストの `.git`、認証情報、追跡外の個人設定は
コピーしません。ソースは読み取り専用、結果ディレクトリだけ書き込み可能で共有します。
Cirrus Labsイメージの公開初期認証情報 `admin/admin` は、この使い捨てVMへのSSHに使用します。

VM内では `guest.sh` が次を実行します。

1. OS・CPU・BrewfileのSHA-256を記録し、VMのAPFS領域を拡張
2. Command Line Tools・Homebrewの準備と、baseイメージにあるnpm版Yarn/pnpmの整理と、Nodeの事前更新
3. Formula/Cask/VS Code拡張/Go/npmを含む `brew bundle` の実導入
4. `brew bundle check` で最終状態を検証
5. 新規HOMEで初回シェルを検証
6. そのHOMEにmiseのランタイムを導入し、Node・Python・Denoの起動を検証

導入失敗時も、可能ならシェルの検証まで実行します。全フェーズが成功した場合だけ
終了コード0になります。ログ・各フェーズの終了コード・導入済みバージョンは
`.validation/<VM名>/` に残します。VMは終了時に停止し、調査用にディスクを保持します。
不要になったVMは、記録された名前を確認して `tart delete <VM名>` で削除できます。
ホストの他のVMを自動で削除・上書きしません。

ダウンロード済みで未使用のVMから開始する場合は、次のようにします。
出力先は新しいディレクトリを指定してください。

```bash
MACOS_VM_PRECLONED=1 MACOS_VM_NAME=your-unused-vm \
  bash tests/macos/vm.sh .validation/another-run
```

baseイメージにはユーザー・SSH・開発用ツールが事前設定されています。
購入直後のSetup Assistant、MDM制限、GUI認証やドライバー権限の検証は別途必要です。

## 既存Macから移行する場合の注意

BrewfileはCorepack経由のYarn/pnpmに統一しています。Homebrew版Yarnを既に
導入している場合は、`command brew unlink yarn` で既存リンクを退避してから
`command brew install corepack` を実行します。切り替えを確認したら
`command brew uninstall yarn` で旧パッケージを削除します
（残すと自動Brewfile更新で再び含まれます）。Yarnのバージョンは各プロジェクトの
`packageManager` 設定で指定してください。

OpenVPN Connect等のPKG形式のアプリは管理者権限が必要です。実機での導入は
パスワードを入力できるターミナルで実行してください。Cirrus Labsのbase VMは
管理者ユーザーでの検証用です。認証に失敗した場合も合格として扱いません。
