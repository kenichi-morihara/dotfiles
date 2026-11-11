# モジュール構成と移行

各 modules/<名前>/ は設定・スクリプト・テスト・依存宣言・ライセンスを持ちます。
このディレクトリだけを新しいリポジトリのルートへコピーして単体利用できます。

| モジュール | 管理するもの |
| --- | --- |
| [window-manager](../modules/window-manager/README.md) | ウィンドウ配置・キーボード操作 |
| [terminal-configs](../modules/terminal-configs/README.md) | ターミナルの見た目・表示操作 |
| [shell-environment](../modules/shell-environment/README.md) | Zsh・検索・履歴・プロンプト |
| [runtimes](../modules/runtimes/README.md) | mise の言語設定 |
| [claude-work-tools](../modules/claude-work-tools/README.md) | Claude の仕事用コマンド変換 |
| [claude-statusline](../modules/claude-statusline/README.md) | Claude の利用量・PR表示 |
| [pi-work-config](../modules/pi-work-config/README.md) | Pi と Claude CLI の接続 |
| [dark-modern-rose](../modules/dark-modern-rose/README.md) | VS Code テーマ・構文・検証 |
| [editor-configs](../modules/editor-configs/README.md) | VS Code と Cursor のユーザー設定 |
| [macos-preferences](../modules/macos-preferences/README.md) | macOS・IME・アプリ設定 |
| [windows-preferences](../modules/windows-preferences/README.md) | Windows のオーバーレイ・常駐設定 |
| [omarchy-preferences](../modules/omarchy-preferences/README.md) | Omarchy・Hypridle 設定 |

## 正本と適用先

各モジュールの home/ は chezmoi の配布元です。ルートの home/ は、同じ配布先名を保ってモジュールを参照するテンプレートです。
設定を編集するときは modules 内の正本を変更し、ルートで make diff / make apply を実行します。
ルートの chezmoi edit / re-add は参照テンプレートを編集・置換するため、モジュールの正本を直接編集してください。

| 編集する場所 | 配布先 |
| --- | --- |
| window-manager/home/dot_config/karabiner/ | ~/.config/karabiner/ |
| terminal-configs/home/dot_config/ghostty/ | ~/.config/ghostty/ |
| shell-environment/home/dot_config/zeno/ | ~/.config/zeno/ |
| runtimes/home/dot_config/mise/ | ~/.config/mise/ |
| dark-modern-rose/home/dot_vscode/extensions/ | ~/.vscode/extensions/ |
| editor-configs/home/dot_cursor/ | ~/.cursor/ |
| claude-statusline/home/dot_claude/ | ~/.claude/ |
| windows-preferences/home/dot_config/windows/ | ~/.config/windows/ |

各モジュール内で make apply / check / test を実行できます。window-manager の単体既定は JIS、KEYBOARD_LAYOUT=us で US を選べます。
Homebrew を利用する場合は make packages を実行します。OS 固有のアプリ処理や追加ターゲットは各 README を参照してください。

## 既存端末の引継ぎ

ルートの初回退避スクリプトは移動せず、内容も維持しています。構成移動だけで初回バックアップを繰り返さないようにしています。
旧 scripts/ の入口はモジュールへ委譲し、既存の make コマンドも引き継ぎます。

Claude の登録先、Pi の設定・セッション、アプリ別バックアップの保存先は既存の場所を使います。
Claude の個人設定は担当項目だけを排他制御付きでマージします。ルートの make apply でも、仕事用フックと status line を併用できます。

brew の Git 自動同期、profile、個人 repo の準備、適用履歴・復元と VM テストは全体運用としてルートに置きます。
旧 Prezto 設定は legacy/ に保管しています。
