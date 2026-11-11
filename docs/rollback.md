# 適用履歴と復元

コマンドはリポジトリのルートで実行します。

今の Mac に残っているバックアップは `make rollback-legacy` で確認できます。
`.backup` の連番には、以前の dotfiles が含まれることがあります。
例えば `.zshrc` は `diff -u ~/.zshrc ~/.zshrc.backup` と
`zsh -n ~/.zshrc.backup` で候補を確認できます。
復元する場合は、現行ファイルを別名で保存してから、確認済みの候補を戻してください。
開いているターミナルを残し、新しいウィンドウで zsh の起動と PATH を確認します。
既存バックアップがない設定の導入前の値は、導入前の別のバックアップが必要です。

今後の適用を記録する場合は、通常の操作を `make tracked ACTION=...` 経由で実行します。
初回の `macos-init` を含めて環境全体を戻す必要がある場合は、先に Time Machine で
バックアップを完了し、Homebrew、アプリ、ランタイム、開発用ディレクトリの保存先が
対象に含まれることを確認してください。
[Apple のバックアップ復元手順](https://support.apple.com/en-ie/102551)

```sh
make tracked ACTION=setup PROFILE=core
# 設定だけ試す場合は make tracked ACTION=apply
make rollback-plan RUN=表示された実行ID
make rollback RUN=表示された実行ID TARGET=.zshrc
# 全ファイルを対象にする場合は TARGET を省略
```

- 記録は `~/.local/state/dotfiles/rollback/` に保存します。設定ファイルの内容を含むため、共有時は必要な部分だけを取り出してください。適用・復元中は、別の適用操作や対象ファイルの編集を止めてください。
- 自動復元は、その実行で変更した chezmoi 配布先のファイル、リンク、ディレクトリのモードを対象にします。現在の状態が適用直後と違う項目は保留します。新規ディレクトリは空になった場合に削除します。ACL・拡張属性・所有者は記録しません。親がシンボリックリンクの構成では記録前に停止するので、その構成では事前バックアップを使ってください。
- アプリ内設定と macOS 設定は JSON の `reference_before` / `reference_after` を参照して手動で戻します。`ACTION=apply-system` では Dock、Spotlight、電源などを記録します。Rectangle はショートカット、Nani は既存バックアップに含まれる項目、iTerm2 は変更されたプロファイルと既定プロファイルを照合します。Dock・電源・入力ソースは macOS のシステム設定で元の値に戻します。
- Homebrew、VS Code、ghq は確認できた追加候補を表示します。mise や npm は記録の前後を比較してください。削除する前に、現在の依存関係やリポジトリの作業内容を確認します。パッケージの更新、cask インストーラーの副作用、chezmoi 自体の状態は自動復元の対象外です。取得できなかった記録は JSON の `status` または `unavailable` で確認できます。
- `make setup`、`make apply`、`chezmoi apply` を直接実行する場合、この復元記録は作られません。

Claude の個人設定 JSON はモジュール間で共有するため、適用履歴では chezmoi 管理対象に加えて ~/.claude/settings.json も記録します。復元時は他のファイルと同じ競合確認を行います。
