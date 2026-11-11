# ターミナルの見た目・表示操作

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## 配布対象
Ghostty、Alacritty、iTerm2 の配色・フォント・表示操作を管理します。iTerm2 の通常設定は scripts/macos/iterm2.json、Dynamic Profile は home/private_Library 以下にあります。
Alacritty は Omarchy のテーマが存在する場合に取り込み、それ以外は Alacritty の既定配色を使います。
macOS では iTerm2 の対象項目も確認・適用します。変更が必要で iTerm2 が起動中の場合は、Terminal.app などから実行してください。
