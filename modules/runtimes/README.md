# mise の言語設定

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## バージョン指定
home/dot_config/mise/config.toml を編集して make apply で配布します。make install で指定したランタイムを導入します。
プロジェクトの mise 設定と Ruby の .ruby-version を尊重します。
