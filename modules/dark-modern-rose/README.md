# VS Code テーマ・構文・検証

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux, windows です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## 拡張と検証
拡張本体は home/dot_vscode/extensions/kenichi-morihara.dark-modern-rose-1.0.0 にあります。
tests/fixtures、拡張内の samples、tests/vscode_theme のトークン解析・実 VS Code 検証・プレビューを同梱します。
make test-vscode は実 VS Code と ruby-lsp を使います。make preview FILE=/absolute/path/to/sample.rb でターミナルに配色を表示します。
VS Code 本体や追加の文法がない環境では、それらを必要とするテストだけスキップします。
