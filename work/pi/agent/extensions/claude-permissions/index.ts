// pi extension: apply the same allow/ask/deny rules Claude Code uses on this machine.
// Intentionally has no bypass mode, flag, command, or environment override.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { decide, loadRules, settingsFiles, toolTarget } from "./rules.ts";

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    const target = toolTarget(event.toolName, event.input as Record<string, unknown>, ctx.cwd);
    if (!target) return;
    const decision = decide(target, loadRules(settingsFiles(ctx.cwd)), ctx.cwd);
    const label = `${target.tool}: ${target.value}`;
    if (decision === "deny") {
      return { block: true, reason: `Claude の権限設定で拒否されています（${label}）` };
    }
    if (decision === "ask") {
      if (!ctx.hasUI) return { block: true, reason: `確認が必要ですが UI がありません（${label}）` };
      const ok = await ctx.ui.confirm("実行を許可しますか？", label);
      if (!ok) return { block: true, reason: `ユーザーが拒否しました（${label}）` };
    }
  });
}
