# ウィンドウ配置・キーボード操作

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## キーボードとウィンドウ
make apply KEYBOARD_LAYOUT=us で US、KEYBOARD_LAYOUT=jis で JIS を選べます。単体利用の既定は JIS です。dotfiles からは既存の端末設定を渡します。
Rectangle の宣言は scripts/macos/rectangle.sh、Karabiner の正本は home/dot_config/karabiner/karabiner.json.tmpl にあります。
Raycast の呼び出しは Karabiner に含め、ターミナルアプリの表示キーは terminal-configs が担当します。
