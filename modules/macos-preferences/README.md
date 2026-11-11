# macOS・IME・アプリ設定

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## 個別に適用する項目
make apply は Nani と Google IME の対象設定を、導入済みアプリについて適用します。make check は同じ項目を読み取り確認します。
make system と make check-system は Dock・Spotlight・電源等のシステム設定、make touchid は sudo Touch ID、make docker と make check-docker は Docker Desktop の割当メモリを扱います。
システム項目と Docker のリソース値は明示的な操作として分けています。設定の宣言・処理は scripts/macos 内で完結しています。
iTerm2 の既定プロファイルは terminal-configs が担当します。

手動の初期準備は bash scripts/macos/init.sh、旧一括導入は bash scripts/macos/setup.sh core で利用できます。
