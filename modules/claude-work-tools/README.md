# Claude の仕事用コマンド変換

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## 明示的な有効化
単体の make apply は STANDALONE=1 を使って導入し、通常の claude にフックを登録します。仕事用 profile を別途作る必要はありません。
dotfiles からの make claude-admin-setup と make claude-admin-default は従来の profile 判定を使います。
既存の ~/.config/dotfiles/claude-admin と ~/.local/bin/claude-admin をそのまま更新し、個人設定とバックアップを保持します。
settings.json の permissions.allow と hooks.PreToolUse に自分の項目だけを追加します。claude-statusline と同じロックを使うため、並行適用でも他方の項目を保持します。
make check は通常の claude への登録とインストール済みファイルを確認します。認証は公式 Claude CLI が管理します。
Bash の解析には scripts/requirements.txt の bashlex を使います。インストーラーが専用の仮想環境に取得します。
