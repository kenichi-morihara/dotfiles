# 個人用・仕事用・端末別の profile

コマンドはリポジトリのルートで実行します。

profile 操作には **Python 3.11 以上**が必要です。新規 Mac は `make macos-init` と
Homebrew の PATH 設定後、必要なら `command brew install python` で準備します。
別の Python を使う場合は各 make に `PYTHON=/path/to/python3` を指定してください。
直接 chezmoi を実行する場合は `python3` を使います（変更は
`DOTFILES_PROFILE_PYTHON=/path/to/python3 chezmoi apply`）。

```sh
# 個人端末
make profile-select NAME=personal
make profile-show
make setup-plan                 # 実効設定と導入予定の表示のみ
make setup                      # パッケージ→設定→ランタイム→repoと開発依存

# 会社端末（IDは任意。設定ファイルはGit管理）
cp profiles/work/example.toml profiles/work/company-laptop.toml
# profiles/work/company-laptop.toml を編集
make profile-select NAME=work/company-laptop
make setup-plan
make setup
```

選択は `${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles/profile` に保存します。
`profile-select` は選択の保存だけを行い、導入や設定適用はしません。
profile の TOML を編集すると、次の操作で再読込します。Git 管理する設定に認証情報を
含めず、秘密情報は既存の `~/.zshrc.local` 等に置いてください。

設定は `profiles/common.toml` → `personal.toml` / `work.toml` →
`profiles/work/<端末ID>.toml` の順に適用します。テーブルはマージし、リストは置換します。
会社ごとに複数端末がある場合も、`会社-端末` のような ID で区別できます。
端末 ID に使える文字は英数字・ハイフン・アンダースコアです。
仕事用の既定だけを使う場合は `NAME=work` を選べます。

| 設定 | 個人用 | 仕事用 |
| --- | --- | --- |
| Homebrew の構成 | full | core |
| キーボードの既定 | JIS | US |
| 追加パッケージ | gmailctl | なし |
| repo | personal-ops / personal-knowledge / mac-security-audit | なし |

端末設定では `package_profile = "core"` / `"full"`、`keyboard_layout = "jis"` /
`"us"`、追加 Homebrew formula の `packages`、`casks`、`repos`、
`knowledge_features` を指定できます。`repos` は `host/owner/repo` のリストです。
今回の3件以外の repo は checkout のみを行います。

```toml
# profiles/work/company-laptop.toml の例
packages = ["jq"]
casks = []
repos = ["github.com/example-company/example-repo"]
keyboard_layout = "us"
```

`make packages` / `make packages-check` は選択済み profile の構成と追加パッケージを使います。
`PROFILE=core/full` は従来どおり構成の明示指定として使えます（追加分は維持）。
未選択なら従来どおり core です。`make setup` は profile 未選択の場合に停止します。
選択解除は上記の `dotfiles/profile` ファイルを削除してください。
profile を切り替えても、以前に取得した repo やパッケージは削除しません。

`make init` / `make apply` では、既存の chezmoi `[data].keyboardLayout` を優先します。
profile の既定に追従させる場合は `chezmoi edit-config` でこの項目を削除してください。
profile の既定はこの項目に固定保存しないため、再初期化しても用途別の既定に追従します。

repo だけを準備する場合は、ランタイム導入後に `make repos` を使います。
`ghq list --full-path` で既存 checkout を確認し、不足分だけ `ghq get` で取得します。
既存の checkout の移動や自動 pull は行いません。

- personal-ops: `ai-tasks/` で `mise exec -- npm ci` を実行し、未導入なら gmailctl を導入します。
- personal-knowledge: `.venv` を作成し、`requirements-mcp.txt` を導入します。
  `knowledge_features = ["capture", "ledger"]` を明示すると、撮影用 Python 依存と会計用の専用環境も準備します。
  OCR バイナリ・撮影キーの生成は、別途 repo 側の `make capture-setup` で行います。
- mac-security-audit: checkout と Python の利用確認を行います。

認証設定、常駐起動、DB 初期化、Gmail 等への反映は行いません。
失敗した場合は停止するため、原因を修正して同じコマンドを再実行してください。
一括導入と profile のパッケージ導入は macOS 対応です。
Linux は既存の OS 別パッケージ導入・設定配布・ランタイム導入後に `make repos` を使えます。

profile 選択中は Homebrew ラッパーによる共通 Brewfile の自動更新・コミット・push を停止します。
追加したパッケージは profile の `packages` / `casks` に明示してください。
未選択端末では従来の自動更新が継続します。
