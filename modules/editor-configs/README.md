# VS Code と Cursor のユーザー設定

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux, windows です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## エディタ設定
VS Code のユーザー設定、Cursor のユーザールール、Cursor Agent の確認・ログイン補助を含みます。
CSS の追加設定は .vscode/custom.css に保管しています。make cursor-setup、make cursor-login で Cursor Agent を確認・認証できます。
テーマそのものは別の dark-modern-rose モジュールとして配布できます。利用するテーマ名はユーザー設定で選択します。
