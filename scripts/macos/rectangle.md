# Rectangle

リポジトリのルートで以下を実行して、Rectangleを含むアプリ設定をまとめて適用する。

```sh
make apply-apps
```

| 操作 | キー |
| --- | --- |
| 左半分 | Control + Option + Command + ← |
| 右半分 | Control + Option + Command + → |
| 最大化 | Control + Option + Command + ↑ |
| 元のサイズに戻す | Control + Option + Command + ↓ |
| 前のディスプレイへ | Control + Option + Shift + Command + ← |
| 次のディスプレイへ | Control + Option + Shift + Command + → |

Karabiner設定の配布後は、Control + Option + Commandの代わりにCaps Lockを
押しながら操作できる（例：左半分はCaps Lock + ←、画面移動はCaps Lock + Shift + ←/→）。

宣言は `rectangle.sh` の `SHORTCUTS` 内で管理する。繰り返し実行しても同じ設定になる。
この6項目以外の設定は変更しない。`make apply` ではmacOSの場合にファイル配布後に実行する。
`chezmoi apply` 単体からの自動実行は行わない。
起動中の場合は終了して適用後に再起動する。終了中の場合は起動しない。

適用前の設定は `~/Library/Application Support/Rectangle/dotfiles-backups/` に保存する。
復元する場合はRectangleを終了し、出力されたバックアップパスを使って以下を実行する。

```sh
defaults import com.knollsoft.Rectangle "/path/to/preferences.backup"
open -a Rectangle
```
