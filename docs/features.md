# 設定・機能の棚卸しと独立配布候補

2026年11月11日時点の dotfiles と端末上の作業中ファイルを調べた一覧です。対象はこの dotfiles の内容です。
`master` の機能と、別ブランチ・未コミットの追加機能を区別しています。追加機能の実装は、この Makefile・資料整理の PR には含めていません。

ここでいう `window-manager` は、macOS のウィンドウ配置・キーボード操作をまとめる切り出し候補の仮称です。独立した同名リポジトリは今回確認した範囲にはなく、Windows OS 向けの設定は別項目として扱います。

## master にある設定・機能

| 分類 | 設定・機能 | 主な実装場所 | 実行・配布と依存 |
| --- | --- | --- | --- |
| 設定配布 | chezmoi による OS 別配布、初回の既存設定退避、リンクの通常ディレクトリへの移行、競合検出、差分・一致確認 | `home/.chezmoi*`、`scripts/link.sh`、`make/core.mk` | chezmoi、初回退避用 Python。配布対象は `home/` |
| 用途・端末管理 | common → personal / work → 会社端末別の設定合成、JIS / US の既定、追加パッケージ・repo の選択 | `profiles/`、`scripts/common/profiles.py`、`home/.chezmoitemplates/profile.json.tmpl` | Python 3.11 以上。選択は端末の `dotfiles/profile` に保存 |
| パッケージ導入 | macOS の core / full、Homebrew 宣言、追加 formula / cask、Arch Linux の yay パッケージ | `scripts/macos/brew.sh`・`.Brewfile*`、`scripts/linux/` | Homebrew または yay。profile 導入は macOS 対応 |
| パッケージ同期 | brew 操作後の Brewfile 更新、Git 同期、profile 選択中の自動更新停止 | `scripts/macos/brew.zsh` | Zsh、Git、dotfiles の remote。個人の運用ルールに依存 |
| Zsh の基本環境 | 履歴、補完、候補表示、構文強調、履歴検索、ディレクトリ移動、sudo・展開・Git の補助 | `scripts/common/.zshrc`・`zinit.zsh`・`keybindings.zsh` | Zsh、zinit と各プラグイン。mise と starship の初期化を含む |
| 検索・移動とスニペット | zeno、ghq の repo 選択、fzf プレビュー、Cursor を開く操作、Git / Docker の短縮入力、ranger 連携 | `scripts/common/zeno.zsh`・`zeno-project-preview.sh`、`home/dot_config/zeno/`・`ranger/` | Deno、fzf、ghq、Lua、ranger。bat / eza があればプレビューに利用 |
| シェル計測・通知 | 初回 zeno 利用時の遅延計測、再読込、macOS 通知 | `scripts/common/latency.zsh`・`latency.md`、`scripts/macos/notify.zsh` | Zsh のフック、macOS 通知。初期化の重複防止を含む |
| ターミナル | Ghostty の配色・フォント・表示操作、iTerm2 の通常 / ホットキープロファイル・Dynamic Profile、Alacritty、starship | `home/dot_config/ghostty/`・`alacritty.toml`・`starship.toml`、`scripts/macos/iterm2.*`、`home/private_Library/.../iTerm2/` | 各ターミナル、HackGen 系フォント。Alacritty の配色は Omarchy のテーマファイルを参照 |
| 言語ランタイム | Node・Python・Go・Deno・Lua・Ruby・Corepack の指定と mise の起動設定 | `home/dot_config/mise/config.toml`、`scripts/common/.zshrc` | mise。プロジェクト別の指定と共存する |
| ウィンドウ・キー操作 | Rectangle の左右分割・最大化・復元・ディスプレイ移動、Karabiner の配列と入力切替、Raycast Clipboard History の呼び出し | `scripts/macos/rectangle.*`、`home/dot_config/karabiner/karabiner.json.tmpl` | Rectangle、Karabiner、Raycast。キーボード選択は profile / chezmoi と連携 |
| 日本語入力 | ABC / Google 日本語入力の有効化と選択、ライブ変換の設定 | `scripts/macos/input-sources.*`、`scripts/macos/defaults.sh` | Swift、Carbon、Google IME。キー操作の配布とは適用経路が異なる |
| macOS システム | Dock、Spotlight、キーリピート、バッテリー表示、電源・スリープ、sudo Touch ID、初期セットアップ | `scripts/macos/defaults.sh`・`sudo-touchid.sh`・`init.sh`・`setup.sh` | defaults、pmset、mdutil、sudo。一部は OS 権限が必要 |
| macOS アプリ | Nani の翻訳ショートカット・テーマ等、Docker Desktop の割当メモリ、複数アプリの適用・確認 | `scripts/macos/nani.*`・`docker.sh`・`apps.sh` | Nani の SQLite、Docker の設定 JSON、各アプリ。対象項目の比較・バックアップを含む |
| Claude の共通設定 | テーマ、モデル・コンテキスト・5時間 / 7日利用量を表示する status line | `home/dot_claude/settings.json`・`executable_statusline.sh` | Claude Code、Bash、jq。仕事用の自動許可とは別の機能 |
| Cursor | ユーザー向け TDD ルール、Cursor Agent CLI の確認・ログイン補助 | `home/dot_cursor/rules/`、`scripts/common/setup-cursor-agent.sh` | Cursor。ルールの適用範囲はユーザー設定 |
| VS Code | ユーザー設定、Dark Modern Rose テーマ、Ruby / ERB 向け構文の色分け、カスタム CSS | `home/dot_vscode/extensions/kenichi-morihara.dark-modern-rose-1.0.0/`、`home/private_Library/.../Code/User/settings.json`、`.vscode/custom.css` | VS Code。拡張のコードとエディタ全体の設定を分離できる |
| Linux デスクトップ | Hypridle と Omarchy のスクリーンセーバー・サスペンド切替 | `home/dot_config/hypr/`・`omarchy/` | Hyprland / Omarchy。Alacritty のテーマもこの環境に依存 |
| Windows OS | Game DVR / Game Bar、NVIDIA Overlay、Armoury Crate の常駐設定 | `home/dot_config/windows/`、`scripts/windows/configure.ps1` | PowerShell、レジストリ、サービス・タスク。機種・アプリに固有の設定を含む |
| 開発 repo の準備 | ghq checkout、個人用 repo の開発依存導入、任意の撮影・会計用依存 | `scripts/common/profiles.py`、`profiles/personal.toml` | ghq、mise、Python、npm 等。個人 repo 名と個別のセットアップ手順を持つ |
| 検証環境 | 一時 HOME と偽コマンドによるテスト、macOS / Linux CI、macOS VM・シェル起動時間・再読込の検証 | `tests/`、`.github/workflows/test.yml` | Python、Git、Zsh、Ruby、chezmoi。VM 検証は Tart と macOS に依存 |
| 旧設定 | Prezto の設定とバックアップ、旧パッケージ出力スクリプト | `scripts/.zpreztorc*`・`.zshrc.prezto.backup`・`yay-export.sh` | 現行の Zsh 入口は zinit。新しい配布物に含める範囲を選ぶ必要がある |

## 別ブランチ・ローカルで追加されている機能

この表の場所は端末上の作業ツリーのパスです。この整理 PR に、その実装ファイルが追加されていることを示す表ではありません。

| 分類 | 設定・機能 | 端末上の場所 | 独立時の主な依存 |
| --- | --- | --- | --- |
| 仕事用 Claude | Git / Docker Compose を専用コマンドへ変換する PreToolUse、自動許可、管理者用起動、通常の claude への端末ローカル登録 | `work/claude-admin/`、`tests/test_claude_admin.py` | Claude CLI、Python 仮想環境、bashlex、Git / Docker、仕事用 profile の保存先 |
| 仕事用 Pi | Pi と Claude CLI 接続の固定バージョン導入、会社用設定・セッション、通常の pi からの起動 | `work/pi/`、`tests/test_pi.py` | Node / mise、Claude Team ログイン、仕事用 profile。Pi 自体は外部依存 |
| 適用履歴・復元 | 適用前後のファイルとアプリ状態の記録、変更項目の復元、既存バックアップの調査 | `scripts/common/rollback.py`、`tests/test_rollback.py` | chezmoi の管理対象、dotfiles の操作名とルート、macOS アプリの状態取得 |
| VS Code テーマ拡張 | Ruby の追加構文・データ領域の色分け、サンプル、実 VS Code / ruby-lsp 検証、ターミナルプレビュー | `home/dot_vscode/extensions/.../`、`tests/vscode_theme/`、`tests/fixtures/` | Node、VS Code、文法・サンプル・テストが複数ディレクトリに分散 |
| ターミナル調整 | Ghostty のグローバル表示キー・全角フォント指定等 | `home/dot_config/ghostty/config` の未コミット差分 | terminal と window-manager のショートカットの担当を決める必要がある |
| キー操作調整 | Karabiner の US 修飾キーと配列操作の更新、関連する Rectangle の案内 | `home/dot_config/karabiner/karabiner.json.tmpl`、`scripts/macos/rectangle.md` 等の差分 | 既存の JIS / US 選択・IME・端末操作との組み合わせ |
| Claude 表示拡張 | status line に PR・関連 Issue のリンクを表示 | `home/dot_claude/executable_statusline.sh` の差分 | GitHub CLI、Git、作業ディレクトリとブランチごとのキャッシュ |
| ランタイム調整 | Ruby のプロジェクト別バージョンファイル対応 | `home/dot_config/mise/config.toml` の差分 | mise と各プロジェクトの `.ruby-version` |

## 独立リポジトリとして配布する場合のまとまり

以下の名前は仮称です。現段階は棚卸しと境界の検討で、リポジトリ分割や配布の実装は行っていません。

| 配布候補 | 含める機能 | 分けておくもの | 現在の結合を解く作業 |
| --- | --- | --- | --- |
| window-manager | Rectangle、Karabiner、Raycast のキー呼び出し | ターミナルの配色・フォント、日本語入力ソースの設定 | JIS / US 選択を独立した入力にする。ターミナル表示キーとの重複を整理し、ウィンドウ操作の適用・確認を単独で提供する |
| terminal-configs | Ghostty、iTerm2、Alacritty、フォントと配色 | Zsh プラグイン、mise の言語バージョン | iTerm2 の適用スクリプトとテストを同梱する。Omarchy の外部テーマ参照、macOS defaults 内の iTerm2 GUID、表示キーの担当を明示する |
| shell-environment | Zsh、zinit、zeno、starship、ranger、通知・遅延計測 | ターミナルアプリの設定、個人 repo の自動取得 | checkout 内の相対参照をパッケージ内に閉じる。Deno / Lua / ghq 等の必要条件と、個人向けスニペットを設定値として分ける |
| claude-work-tools | 仕事用の変換フック、専用コマンド、導入・通常起動への登録 | Claude の共通 status line、Pi | 仕事用 profile ファイルへの依存を独立した有効化設定に替える。既存個人設定とのマージ・復元・解除を一つの配布物で完結させる |
| claude-statusline | 利用量表示、任意の PR / Issue 表示 | 仕事用の自動許可ルール | status line の実行ファイルと登録方法を同梱し、GitHub 連携の任意依存を明記する |
| pi-work-config | Pi の導入・Claude CLI 接続・会社用設定 | Claude の承認フック、シェル全体の初期化 | dotfiles の profile と mise を必須にするか、通常の Node と独立した設定で導入できるようにするかを決める |
| dark-modern-rose | VS Code テーマ、構文注入、サンプル、配色テスト | エディタ全体のユーザー設定、カスタム CSS | 拡張とテストを同じルートにまとめ、dotfiles 内の絶対・相対パスを外し、VSIX にする入口を用意する |
| macos-preferences | Dock・電源・Spotlight、IME、Touch ID、必要に応じてアプリ別設定 | ターミナル・ウィンドウ設定、言語環境 | システム・IME・アプリを個別に選択できる入口と宣言に分ける。機種固有のメモリや電源の値を引数・プリセットにする |
| windows-preferences / omarchy-preferences | 各 OS 固有の宣言と適用処理 | macOS 設定、共通シェル | OS ごとに分け、機種固有のサービス名・アプリ名を選択可能にする |
| dotfiles 本体 | profile、採用する配布物・バージョンの選択、導入順、適用状態と検証 | 各配布物の内部処理 | 各リポジトリを利用する薄い入口として残す。Homebrew 同期や個人 repo の準備は個人運用の層に置く |

window-manager・terminal-configs・shell-environment は別々の関心事を持ちます。ウィンドウ配置、ターミナルの表示・見た目、ターミナル内の操作をそれぞれの担当にすると、ショートカットと配色を重複管理する箇所を減らせます。

## 公開可能な配布物にするために残ること

- 各候補のソース・設定例・テスト・導入案内を、その候補のディレクトリだけで揃える。現在の単体テストは dotfiles のルート構成を前提にしている箇所がある。
- dotfiles のルート、profile 保存先、ユーザー名、個人 repo、会社向け値への依存を、入力とサンプルへ分ける。認証情報や端末で生成されたセッションは配布対象に含めない。
- 個別に導入・確認・更新・解除する方法を決める。chezmoi の初回退避やアプリ別バックアップに依存している処理は、単体での既存設定の扱いも用意する。
- LICENSE と依存元の表示を各配布物に揃える。現状の README は MIT と記載しているが、ranger 由来ファイルには原プロジェクトのライセンス適用が明記されており、配色や文法を含めて元の条件を確認する必要がある。

現時点では独立性の異なる候補が混在しています。まず window-manager、仕事用 Claude、terminal-configs の三つを個別に設計し、共通シェルや OS 設定をどこまで同梱するか決めると、移動するファイルと依存関係を具体化できます。
