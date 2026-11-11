# Claude の利用量・PR表示

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## 個人設定の更新
status line の実体を ~/.claude/statusline.sh に配布し、settings-fragment.json の theme と statusLine だけを個人設定にマージします。
permissions や hooks は保持します。claude-work-tools と同じロックを使い、変更前の JSON を XDG_STATE_HOME/claude-statusline/backups に保存します。
GitHub CLI が使える場合は PR・関連 Issue をキャッシュ付きで表示します。
