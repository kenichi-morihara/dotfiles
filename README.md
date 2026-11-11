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
| 用途・端末を選ぶ | `make profile-select NAME=personal` |
| 導入予定を確認する | `make setup-plan` |
| テストする | `make test` |
| 全コマンドを見る | `make help-all` |

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

## どこを編集するか

| 場所 | 管理するもの |
| --- | --- |
| `home/` | chezmoi で配布するファイル。OS ごとの対象は `.chezmoiignore` に定義 |
| `profiles/` | 共通 → 個人用 / 仕事用 → 端末別のパッケージ・キーボード・repo |
| `scripts/common/` | 共通 Zsh モジュール、profile 処理 |
| `scripts/macos/`・`linux/`・`windows/` | OS 固有の導入・アプリ・システム操作 |
| `make/` | `core.mk` が基本操作、`maintenance.mk` がテストの入口 |
| `tests/` | 一時 HOME・偽コマンドによる検証、macOS の実機検証手順 |
| `docs/` | 用途別の詳しい手順 |

`.chezmoiroot` は配布対象を `home/` に限定します。
シェルの入口 `home/dot_zshrc.tmpl` は checkout 内の `scripts/common/.zshrc` を読み込みます。
端末固有の秘密情報やシェル設定は `~/.zshrc.local` に置きます。

Make ターゲットを追加するときは該当する `.mk` に置き、`## 説明` を付けると `make help-all` に表示されます。
既存アプリの設定処理は `scripts/macos/apps.sh` にまとめます。

## 詳しい手順

| 内容 | 案内 |
| --- | --- |
| インストール・設定更新・Linux / Windows・トラブル対処 | [導入手順](docs/setup.md) |
| 個人用・仕事用・端末別の選択 | [profile](docs/profiles.md) |
| キーボード・IME・アプリ・macOS システム設定 | [macOS](docs/macos.md) |
| 自動テスト・新規 HOME / VM | [テストと動作確認](docs/testing.md) |
| 設定・機能の一覧と独立配布候補 | [機能棚卸し](docs/features.md) |

## ライセンス

MIT
