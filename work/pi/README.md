# pi coding agent（会社用）

会社端末で [pi coding agent](https://github.com/earendil-works/pi) を使うための設定です。
共通設定（`home/` 以下を chezmoi が配る分）には含めず、このディレクトリだけで完結させています。
`make apply` / `make setup` では導入されません。

#corp-it への相談文の下書きは [corp-it-request.md](corp-it-request.md) にあります。

## 手順

```sh
make profile-select NAME=work/<端末ID>   # 会社用 profile（未選択の場合）
make runtimes                            # Node.js 22.19 以上
make pi-setup
pi                                       # 起動して /login → Anthropic（本人が手動で行う）
```

`install.sh` は、会社用 profile が選択されていない場合に停止します。
`~/.pi/agent/settings.json` と `extensions/claude-permissions/` を配置し、差分のある既存ファイルは `.backup` に退避します。
`~/.pi/agent/auth.json`（ログイン情報）には触れず、Git でも管理しません。

## 権限（claude-permissions 拡張）

pi は標準ではツールの実行前に確認しません。この拡張は Claude Code と同じ allow / ask / deny の規則を pi に適用します。

規則は次のファイルから読みます。存在するファイルだけを使い、どのファイルも規則を足すだけで、外すことはできません。

1. `~/.claude/remote-settings.json`（会社の管理設定）
2. `~/ghq/github.com/primenumber-dev/claude-team-operation/settings.json`
3. `~/.claude/settings.json` / `~/.claude/settings.local.json`
4. プロジェクトの `.claude/settings.json` / `.claude/settings.local.json`

| 判定 | 動作 |
| --- | --- |
| deny に該当 | 実行しない |
| ask に該当 | 確認する（UI がなければ実行しない） |
| allow に該当 | そのまま実行 |
| どれにも該当しない | bash・edit・write は確認、read・grep・find・ls は実行 |

- pi のツールは `bash`→`Bash`、`read`/`grep`/`find`/`ls`→`Read`、`edit`/`write`→`Edit` として判定します（`Write(...)` の規則も `Edit` に適用）。
- `&&` `||` `;` `|` でつないだコマンドは区切りごとに判定します。全体を自動で許可するのは、すべての区切りが allow に該当する場合だけです。
- 設定ファイルの JSON が壊れている場合は、すべての操作で確認を求めます（安全側に倒す）。
- pi 標準以外のツール（MCP など）は、この拡張の対象外です。

テスト: `node --test work/pi/agent/extensions/claude-permissions/rules.test.ts`（`make test` でも実行）

## 含めていないもの

- すべてを自動で許可するモード（会社の管理設定 `disableBypassPermissionsMode: "disable"` に合わせています）
- モバイルからのリモート操作（会社の設定で Remote Control が無効です。pi-web・Telegram 連携・Tailscale 経由での操作も含めません）
- 非公式の Anthropic 認証プラグイン（`pi-sub-anthropic` など）

これらが必要な場合は、`claude-team-operation` への PR か #corp-it への相談で方針を変えてもらってください。
