# #corp-it への相談文（下書き）

そのまま貼れる形にしています。【】の部分は送る前に書き換えてください。

---

pi coding agent の利用可否について相談させてください。

**使いたいもの**
- pi coding agent（OSS・MIT ライセンス、https://github.com/earendil-works/pi ）
- Pi と `claude-code-pi` 拡張を、会社用ディレクトリにバージョン固定・`--ignore-scripts` で導入します

**確認したいこと**
1. 会社端末で pi を使ってよいか
2. 公式 Claude Code CLI の `claude -p` を Pi のモデル接続に使ってよいか
   - 認証は公式 CLI の Claude Team ログインを利用します
3. （任意）モバイルからの Remote Control の許可。現在は `allow_remote_control: false` です
   - 用途:【例: 移動中に長時間のタスクの進み具合を確認・承認したい】

**安全面の対応**
- 会社用プロファイルで起動した Pi は、標準ツールを OS ユーザーの権限で確認なしに実行します。
- ログイン情報は公式 CLI が保持します
- 設定一式: 【dotfiles リポジトリの work/pi/ へのリンク】

---

## claude-team-operation に PR を出す場合（Remote Control について）

Remote Control は Claude の組織設定（policy-limits）で制御されています。
そのため、リポジトリの `settings.json` を変えても有効にはなりません。
PR では、方針の変更提案として理由と使い方を書き、管理者に組織設定の変更を依頼する形にしてください。
