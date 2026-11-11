# Dotfiles

macOS・Linux・Windows の設定を管理します。設定配布は chezmoi、パッケージは Homebrew / yay、言語ランタイムは mise が担当します。

## 普段使う操作

リポジトリのルートで `make` を実行すると、よく使う操作を表示します。

| やりたいこと | コマンド |
| --- | --- |
| 設定の差分を見る | `make diff` |
| ファイルとアプリ設定を反映する | `make apply` |
| 反映状態を確認する | `make check` |
| パッケージ・設定・ランタイム・repo をまとめて導入する | `make setup` |
| 用途・端末を選ぶ | `make profile-select` |
| 導入予定を確認する | `make setup-plan` |
| テストする | `make test` |
| 仕事用を含む全コマンドを見る | `make help-all` |

`apply` はファイル → アプリ設定の順に適用し、競合時に停止します。
システム設定は `make apply-system`、ログインシェル変更は `make shell-setup` で個別に実行します。

## 新しい Mac の準備

```sh
ghq get github.com/kenichi-morihara/dotfiles
cd "$(ghq root)/github.com/kenichi-morihara/dotfiles"

make macos-init
# Homebrew の PATH と Python 3.11 以上を準備する
make profile-select NAME=personal
# 会社端末では NAME=work または NAME=work/<端末ID> を指定する
make setup-plan
make setup
```

Command Line Tools や Homebrew の初期準備、既存設定の移行は [導入手順](docs/setup.md) を参照してください。

## ディレクトリ構成

    dotfiles/
    ├── modules/     # 単体導入できる12モジュール
    ├── home/        # 各モジュールを参照するchezmoiテンプレート
    ├── profiles/    # 個人用・仕事用・端末別の選択
    ├── scripts/     # 全体の導入・profile・復元、旧入口の委譲
    ├── make/        # 全体操作とモジュールへの入口
    ├── tests/       # 統合・単体コピー・移行の検証
    ├── docs/        # 全体の手順
    └── legacy/      # 旧Prezto設定など

設定本体は modules 内で編集します。例えば次のように単体で適用できます。

    make -C modules/window-manager apply KEYBOARD_LAYOUT=us
    make -C modules/window-manager check KEYBOARD_LAYOUT=us
    make -C modules/claude-work-tools apply

[各モジュールの担当・単体利用・移行手順](docs/modules.md) を参照してください。

## 詳しい手順

| 内容 | 案内 |
| --- | --- |
| インストール・設定更新・Linux / Windows・トラブル対処 | [導入手順](docs/setup.md) |
| 個人用・仕事用・端末別の選択 | [profile](docs/profiles.md) |
| キーボード・IME・アプリ・macOS システム設定 | [macOS](docs/macos.md) |
| 適用前の記録・バックアップ・復元 | [適用履歴と復元](docs/rollback.md) |
| 自動テスト・新規 HOME / VM・VS Code テーマ | [テストと動作確認](docs/testing.md) |
| Claude の管理者設定・Pi | [仕事用ツール](work/README.md) |

## ライセンス

MIT
