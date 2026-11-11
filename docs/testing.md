# テストと動作確認

コマンドはリポジトリのルートで実行します。

GitHub Actionsの [Tests](../.github/workflows/test.yml) で、push・Pull Request時に
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

検証環境（新規HOME・macOS VM）の作成と実行は [tests/macos/README.md](../tests/macos/README.md)、実行結果は [tests/macos/VALIDATION.md](../tests/macos/VALIDATION.md) を参照してください。

## 新規macOSでの最終確認

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
