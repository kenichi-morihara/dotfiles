// Claude Code-compatible permission rules for pi (pure functions; no pi imports).
// Order matches Claude Code: deny > ask > allow > default (Bash/Edit ask, Read allow).
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { isAbsolute, join, resolve } from "node:path";

export type Decision = "deny" | "ask" | "allow";
export type ClaudeTool = "Bash" | "Read" | "Edit";
export interface Rules {
  deny: string[];
  ask: string[];
  allow: string[];
}
export interface Target {
  tool: ClaudeTool;
  value: string; // bash command, or absolute file path
}

const SEVERITY: Record<Decision, number> = { allow: 0, ask: 1, deny: 2 };
const TEAM_SETTINGS = "ghq/github.com/primenumber-dev/claude-team-operation/settings.json";

// Managed company settings come first; every file only adds rules, none can remove them.
export function settingsFiles(cwd: string, home: string = homedir()): string[] {
  return [
    join(home, ".claude/remote-settings.json"),
    join(home, TEAM_SETTINGS),
    join(home, ".claude/settings.json"),
    join(home, ".claude/settings.local.json"),
    join(cwd, ".claude/settings.json"),
    join(cwd, ".claude/settings.local.json"),
  ];
}

export function loadRules(files: string[]): Rules {
  const rules: Rules = { deny: [], ask: [], allow: [] };
  for (const file of files) {
    if (!existsSync(file)) continue;
    let permissions: Record<string, unknown> | undefined;
    try {
      permissions = JSON.parse(readFileSync(file, "utf8"))?.permissions;
    } catch {
      // Unreadable settings must not silently loosen anything: treat every call as ask.
      rules.ask.push("Bash", "Edit", "Read");
      continue;
    }
    for (const key of ["deny", "ask", "allow"] as const) {
      const list = permissions?.[key];
      if (Array.isArray(list)) rules[key].push(...list.filter((x): x is string => typeof x === "string"));
    }
  }
  return rules;
}

export function toolTarget(toolName: string, input: Record<string, unknown>, cwd: string): Target | undefined {
  const path = typeof input.path === "string" ? input.path : ".";
  const abs = resolve(cwd, expandHome(path));
  switch (toolName) {
    case "bash":
      return { tool: "Bash", value: String(input.command ?? "") };
    case "read":
    case "grep":
    case "find":
    case "ls":
      return { tool: "Read", value: abs };
    case "edit":
    case "write":
      return { tool: "Edit", value: abs };
    default:
      return undefined; // Non-builtin tools are outside Claude Code's rule vocabulary.
  }
}

export function decide(target: Target, rules: Rules, cwd: string, home: string = homedir()): Decision {
  const values = target.tool === "Bash" ? [target.value.trim(), ...splitCommand(target.value)] : [target.value];
  let worst: Decision = "allow";
  let everyAllowed = true;
  for (const value of values) {
    const hit = (key: keyof Rules) => rules[key].some((rule) => matchRule(rule, target.tool, value, cwd, home));
    if (hit("deny")) return "deny";
    if (hit("ask")) worst = max(worst, "ask");
    else if (!hit("allow")) everyAllowed = false;
  }
  // A chained command is allowed only when every segment is allowed
  // ("Bash(ls *)" must not approve "ls && make deploy").
  if (worst === "ask") return "ask";
  if (target.tool === "Read" || everyAllowed) return "allow";
  return "ask";
}

export function matchRule(rule: string, tool: ClaudeTool, value: string, cwd: string, home: string = homedir()): boolean {
  const parsed = /^(\w+)(?:\((.*)\))?$/s.exec(rule.trim());
  if (!parsed) return false;
  const [, ruleTool, spec] = parsed;
  const applies = ruleTool === tool || (tool === "Edit" && ruleTool === "Write");
  if (!applies) return false;
  if (spec === undefined || spec === "" || spec === "*") return true;
  if (tool === "Bash") return commandPattern(spec).test(value.trim());
  return pathPattern(spec, cwd, home).test(value);
}

export function splitCommand(command: string): string[] {
  return command
    .split(/&&|\|\||;|\||\n/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function commandPattern(spec: string): RegExp {
  const normalized = spec.endsWith(":*") ? spec.slice(0, -2) + " *" : spec;
  // A trailing " *" also matches the bare command ("git push" for "git push *").
  const trailing = normalized.endsWith(" *");
  const body = trailing ? normalized.slice(0, -2) : normalized;
  const source = body.split("*").map(escape).join(".*");
  return new RegExp("^" + source + (trailing ? "(?:\\s.*)?" : "") + "$", "s");
}

function pathPattern(spec: string, cwd: string, home: string): RegExp {
  let base: string;
  if (spec.startsWith("~/")) base = join(home, spec.slice(2));
  else if (spec.startsWith("//")) base = spec.slice(1);
  else if (isAbsolute(spec)) base = spec;
  else base = join(cwd, spec);
  const source = base
    .split(/(\*\*\/?|\*)/)
    .map((part) => (part === "**/" ? "(?:.*/)?" : part === "**" ? ".*" : part === "*" ? "[^/]*" : escape(part)))
    .join("");
  // A directory rule also covers everything below it.
  return new RegExp("^" + source + "(?:/.*)?$", "s");
}

function expandHome(path: string): string {
  return path === "~" ? homedir() : path.startsWith("~/") ? join(homedir(), path.slice(2)) : path;
}

function escape(text: string): string {
  return text.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
}

function max(a: Decision, b: Decision): Decision {
  return SEVERITY[a] >= SEVERITY[b] ? a : b;
}
