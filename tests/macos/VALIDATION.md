# macOS検証結果 — 2026-10-19

対象: macOS 26.6.2 (25G83)、Apple Silicon (arm64)。
Brewfileの対象は57 Formula、31 Cask、60 VS Code拡張、8 Go、1 npm（計157項目、依存を除く）、6 tap。

| 検証 | 結果 |
| --- | --- |
| 回帰テスト | 11件成功 |
| VM内で修正後の全パッケージ導入 | 157項目＋6 tap成功、終了コード0 |
| VM内で `brew bundle check` | 全依存充足、終了コード0 |
| VM内の新規HOMEで対話・ログインZsh | 18項目成功、約41.7秒、終了コード0 |
| VM内でmiseランタイム導入・実行 | Node 25.2.1 / Python 3.14.8 / Deno 2.6.5 成功 |
| 既存ホストでの全パッケージ導入 | Corepack/Yarn衝突を修正後、残る未充足はOpenVPN Connectの管理者認証 |

VMの `result.json` は `bundle_exit_code`、`bundle_check_exit_code`、
`shell_exit_code`、`runtimes_exit_code` がすべて0でした。
OpenVPN Connectも、管理者権限が利用できるVM内では導入できています。

シェル検証は、コマンド9種・ウィジェット5種・zenoの準備状態と
Ctrl+G/Tab/Ctrl+Rの割り当てを確認しています。
初回のプラグイン取得コミットは `shell/result.json` に記録しています。

## 実行環境と範囲

Tart 2.41.1、4 CPU、8GB RAM、120GBの論理ディスクで実行しました。
VMイメージは `vm.env` のdigestで固定したCirrus LabsのTahoe baseです。
baseには開発ツールが事前導入されており、導入前の一覧を `installed-before.txt` に記録しています。
ホストのHomebrew・個人設定・認証情報はVMに引き継いでいません。

最初のVM実行で失敗を確認し、修正後に同じVMで再実行して全依存の充足を検証しました。
base固有のnpm版Yarn/pnpmを整理してCorepackに統一し、Nodeを事前更新しています。
各シェル検証は、毎回別のHOME・プラグインキャッシュで実行しました。
購入直後のSetup AssistantやMDM制限、GUI操作・権限の許可、各サービスの起動は対象外です。

## 修正内容

- 既存設定を保持するリンク作成と、繰り返し実行
- Brewfileの読み込み先と、導入済みHomebrewの再インストール回避
- 廃止された `homebrew/bundle` tap・Fig cask指定の削除
- zenoの遅延初期化に対応したキー割り当て
- fzf-tabによるTab上書きと、fzfの不要なコンパイル警告
- CorepackをHomebrew経由に統一して、単体Yarnとの実行ファイル衝突を解消

検証スクリプトは通常の `brew bundle` を使います。
Homebrew 7.0.xのverbose実行ではnpmのNode PATH補完が通らず失敗したため、
実際のセットアップと同じ通常モードで導入を確認しました。

`.tool-versions` と `.config/mise/config.toml` のNode指定は異なります。
今回のホームディレクトリでの `mise install` はNode 25.2.1を選択しました。
ランタイム設定自体は変更していません。

Brewfile SHA-256: `a3eaf4f682a711421ea0b472d7534b0c069cdb8cdac09003582f75df0fca8fbe`

実行環境の構成・再実行手順は [README.md](README.md) を参照してください。
最終VMのログはrepo内の `.validation/vm-20261019-verified/`、
ホストの結果は `.validation/host-20261019/` に保存しています。
途中の失敗ログも `.validation/vm-20261019-full/`・`.validation/vm-20261019-final/` に保持しています。
`.validation/` は生成物としてGit管理対象外です。
VMは停止済みで、ディスクは調査・再実行用に保持しています。

## セットアップ整理の追加検証 — 2026-10-20

- 回帰テスト15件成功。Brewfileのcore/full選択、旧 `.tool-versions` リンクの移行、設定保持を含みます。
- coreプロファイル9 Formulaの `brew bundle check --no-upgrade` 成功。
- 一時HOMEへのmise導入成功。`mise current` と実行バージョンはNode 25.2.1、Python 3.14.8、Deno 2.6.5。
- PTY上の対話・ログインzshの初回起動22.887秒、温まった10回の中央値0.510秒、p95 0.571秒。

起動時間はPTY上でプロンプト表示後の最初のコマンドを受け付けるまでを測定しています。
初回は新規HOMEでプラグイン取得が始まる条件、温まった計測は同じHOMEとプラグインキャッシュを
再利用する条件です。Homebrew本体はホストと共用しています。実測JSONは
`.validation/shell-benchmark-20261020-interactive/`、ランタイム導入ログは
`.validation/shell-benchmark-20261020/runtimes/` にあります（生成物のためGit管理外）。

coreの通常の `brew bundle check` はmiseの更新が必要と判定しました。ホストのmiseは
2026.10.14、Homebrewの現行Formulaは2026.10.15だったため、この検証ではホストに変更を加えず
`--no-upgrade` で導入済み依存を確認しました。

## 依存の整理・機能の準備完了・再読み込み検証 — 2026-10-20

fzfはOSのパッケージ管理に一本化し、zinitからの取得を削除しました。
新規HOMEのプラグイン一覧に `junegunn---fzf` がないことを確認しています。
DenoはmacOSではHomebrew、Arch LinuxではOSパッケージから導入します。
miseのグローバル設定はNode・Pythonに絞り、既存の個人環境のランタイムは削除していません。
coreの分類は全構成のBrewfileから宣言とオプションを読み込む方式に変更しました。

| 検証 | 結果 |
| --- | --- |
| 回帰テスト | 21件成功 |
| coreの実際のDSL評価・依存確認 | 9 Formula、`brew bundle check --no-upgrade` 成功 |
| 新規HOMEでのシェルsmoke | 18項目成功、終了コード0 |
| miseの導入・実行 | Node 25.2.1 / Python 3.14.8 成功 |
| Denoの導入元・実行 | `/opt/homebrew/bin/deno`、2.9.7成功。miseへの重複導入なし |
| 初回プロンプト / 機能の準備完了 | 26.658秒 / 29.538秒 |
| 温まった10回のプロンプト中央値 / p95 | 0.239秒 / 0.254秒 |
| 温まった10回の機能準備中央値 / p95 | 1.199秒 / 1.383秒 |
| 再読み込み | 11シェル × 5回。PATH・fpath・フック・プラグイン登録・キー割り当て維持 |
| zenoサーバー | 各シェルで再読み込み前後のPID集合が同一の1プロセス。正常終了後の残存0 |

機能の準備完了は、zenoの初回利用に相当する `zeno-ensure-loaded` の実行後、
補完関数・履歴検索ウィジェット・zenoの初期化フラグ・ソケットが揃った時刻です。
約0.2秒間隔で判定するため、その間隔とプローブ自体の時間を含みます。
対話候補の選択操作や通知・GUI権限は今回の検証対象外です。

従来のベンチマークは入力描画中のマーカーを拾う可能性があり、起動確認後はシェルを
強制終了していました。今回は実際の出力行だけを認識し、正常終了とサーバーの終了まで
確認しています。旧0.510秒との数値の単純比較はできません。初回値はネットワーク取得を含みます。

実測・再読み込みログは `.validation/refinements-20261020-v3/`、
ランタイム導入ログはその `runtimes/`、smokeの結果は `.validation/refinements-20261020-smoke/`。
zenoの取得コミットは `f6ed8fc16cc32dc110fa4f77a50386624067fbe2` です。
この追加検証は既存macOS上の新規HOMEで実施し、全パッケージのVM再導入やLinuxでの実導入は
行っていません。全構成のパッケージ宣言は、この整理では変更していません。
