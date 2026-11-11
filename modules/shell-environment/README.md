# Zsh・検索・履歴・プロンプト

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## 読み込み
home/dot_zshrc.tmpl はこのモジュール内の scripts/common/.zshrc を読み込みます。mise と starship があれば初期化します。
Zsh プラグイン、zeno、通知・遅延計測をこのモジュール内で完結させています。Homebrew の自動 Git 同期は dotfiles 本体の個人運用として管理します。
make shell-setup でログインシェルを切り替えます。
