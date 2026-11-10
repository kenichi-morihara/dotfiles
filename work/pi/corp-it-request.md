# #corp-it への相談文（下書き）

そのまま貼れる形にしています。【】の部分は送る前に書き換えてください。

---

pi coding agent の利用可否について相談させてください。

**使いたいもの**
- pi coding agent（OSS・MIT ライセンス、https://github.com/earendil-works/pi ）
- npm パッケージ `@earendil-works/pi-coding-agent` を `--ignore-scripts` で導入します

**確認したいこと**
1. 会社端末で pi を使ってよいか
2. Claude Team のサブスクを pi の `/login`（Anthropic OAuth）で使ってよいか
   - Anthropic の規約では、サブスクの OAuth は Claude Code などの自社アプリ向けとされています。規約上の扱いについても確認をお願いします
   - だめな場合、会社として API キーを発行してもらうことはできるか
3. （任意）モバイルからの Remote Control の許可。現在は `allow_remote_control: false` です
   - 用途:【例: 移動中に長時間のタスクの進み具合を確認・承認したい】

**安全面の対応**
- 権限は `claude-team-operation` の ask/deny 規則と、会社の管理設定（remote-settings.json）をそのまま pi に適用する拡張で制御します（deny は実行しない、ask は毎回確認）
- すべてを自動で許可するモードは用意していません
- ログイン情報（`~/.pi/agent/auth.json`）は Git で管理しません
- 設定一式: 【dotfiles リポジトリの work/pi/ へのリンク】

---

## claude-team-operation に PR を出す場合（Remote Control について）

Remote Control は Claude の組織設定（policy-limits）で制御されています。
そのため、リポジトリの `settings.json` を変えても有効にはなりません。
PR では、方針の変更提案として理由と使い方を書き、管理者に組織設定の変更を依頼する形にしてください。
