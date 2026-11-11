# Omarchy・Hypridle 設定

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は linux です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## Omarchy
Hypridle の宣言と、起動時にスクリーンセーバー・サスペンド切替を設定するフックを配布します。
Omarchy / Hyprland を外部依存とします。端末の配色は terminal-configs で管理します。
