// End-to-end colour check in a real VS Code window with ruby-lsp and tsserver running.
//
// Launches VS Code with a throwaway profile (real ~/.vscode/extensions), opens a
// copy of tests/fixtures/vscode_theme/lsp_workspace, waits for ruby-lsp and
// tsserver, then for each theme variant reads the rendered token colours from the
// editor DOM over the DevTools protocol and checks them against EXPECTATIONS.
// Exit code 0 = all pass.
//
// usage: node tests/vscode_theme/e2e.mjs   (env: E2E_RUBY_VERSION, VSCODE_BIN)
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '../..');
const BIN = process.env.VSCODE_BIN || '/Applications/Visual Studio Code.app/Contents/MacOS/Code';
const CLI = path.join(path.dirname(BIN), '../Resources/app/bin/code');
const PORT = 9333 + Math.floor(Math.random() * 500);
const RUBY = process.env.E2E_RUBY_VERSION || '4.0.9';

// Colour roles; each theme maps them to colours (see tests/test_vscode_theme.py).
const BASE = {
  keyword: '#BD93F9', decl: '#DC92B7', class: '#62E1C7', constant: '#74C4FF', variable: '#74C4FF',
  symbol: '#A6B4EE', function: '#F1E4A6', plain: '#E3E1ED', string: '#FFAE92', literal: '#F0A04B',
  control: '#F78FD9',
};
const THEMES = [
  { label: 'Dark Modern Rose', palette: BASE },
];
// file -> [line needle, token, role, nth occurrence on the line]
const EXPECTATIONS = {
  'lineage.rb': [
    ['raise e', 'e', 'variable'],
    ['e.results,', 'e', 'variable'],
    ['rescue Datamart::Error::LoadError => e', 'e', 'variable'],
    ['d_tables.uniq', 'd_tables', 'variable'],
    ['d_tables += Metadata', 'd_tables', 'variable'],
    ['transfer_record: transfer_record', 'transfer_record', 'function', 1],
    ['executed_query: executed_query', 'executed_query', 'function', 1],
    ['custom_variable_expanded_before_load,', 'custom_variable_expanded_before_load', 'function'],
    ['@transfer_record = transfer_record', 'transfer_record', 'variable'],
    ['def load! = nil', 'nil', 'literal'],
    ['def write_disposition_append? = true', 'true', 'literal'],
    ['raise Datamart::Error::QualityCheckViolationError.new(', 'QualityCheckViolationError', 'class'],
    ['if write_disposition_append?', 'if', 'control'],
    ['MAX_TABLES = 100', 'MAX_TABLES', 'constant'],
    ['first(MAX_TABLES)', 'MAX_TABLES', 'constant'],
    ['raise e', 'raise', 'control'],
    ['return head(:no_content)', 'return', 'control'],
    ['return head(:no_content)', 'head', 'function'],
    ['redirect_to root_path and return', 'redirect_to', 'function'],
    ['redirect_to root_path and return', 'return', 'control'],
    ['render json: { ok: true }', 'render', 'function'],
    ['def find_by_code(code)', 'code', 'variable', 0],
    ['def find_by_code(code)', 'code', 'symbol', 1],
    ['def find_by_code(code)', 'code', 'variable', 2],
    ['->(status)', 'status', 'variable', 0],
    ['->(status)', 'status', 'symbol', 1],
    ['->(status)', 'status', 'variable', 2],
  ],
  'component.tsx': [
    ['export const API_URL', 'API_URL', 'constant'],
    ['setQuery(API_URL)', 'API_URL', 'constant'],
    ['enum Status', 'Open', 'constant'],
    ['o.status === Status.Open', 'Open', 'constant'],
    ['o.status === Status.Open', 'Status', 'class'],
    ['o.status === Status.Open', 'o', 'variable'],
    ['o.status === Status.Open', 'status', 'variable'],
    ['const [query, setQuery]', 'query', 'variable'],
    ['const [query, setQuery]', 'setQuery', 'function'],
    ['const [query, setQuery]', 'useState', 'function'],
    ['const visible =', 'visible', 'variable'],
    ['count += visible.length', 'count', 'variable'],
    ['count += visible.length', 'length', 'variable'],
    ['const options =', 'limit', 'symbol'],
    ['new Map<', 'Map', 'class'],
    ['cache = new Map', 'cache', 'symbol'],
    ['type Order = {', 'status', 'symbol'],
    ['store.cache.size', 'cache', 'variable'],
    ['const store = new OrderStore', 'OrderStore', 'class'],
    ['<ul className', 'ul', 'decl'],
    ['<ul className', 'className', 'symbol'],
    ['<Row key', 'Row', 'class'],
    ['<Row key', 'onPick', 'symbol'],
    ['props.order.id', 'props', 'variable'],
    ['props.order.id', 'order', 'variable'],
    ['export function OrderList', 'OrderList', 'function'],
  ],
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function writeSettings(userData, theme) {
  fs.writeFileSync(path.join(userData, 'User/settings.json'), JSON.stringify({
    'workbench.colorTheme': theme,
    'security.workspace.trust.enabled': false,
    'workbench.startupEditor': 'none',
    'window.restoreWindows': 'none',
    'extensions.autoUpdate': false,
    'editor.minimap.enabled': false,
    'typescript.tsserver.log': 'off',
  }));
}

function prepareWorkspace() {
  // Short paths: VS Code's IPC socket path must stay under ~103 chars.
  const base = fs.mkdtempSync(path.join('/tmp', 'dmr-e2e-'));
  const ws = path.join(base, 'ws');
  fs.cpSync(path.join(ROOT, 'tests/fixtures/vscode_theme/lsp_workspace'), ws, { recursive: true });
  fs.writeFileSync(path.join(ws, '.ruby-version'), RUBY + '\n');
  // Extensions dir = the user's extensions, with this theme swapped for the copy under test.
  const theme = path.resolve(process.env.DARK_MODERN_ROSE_EXT
    || path.join(ROOT, 'home/dot_vscode/extensions/kenichi-morihara.dark-modern-rose-1.0.0'));
  if (!fs.existsSync(path.join(theme, 'package.json'))) throw new Error(`theme extension not found: ${theme}`);
  const srcExts = process.env.VSCODE_EXTENSIONS || path.join(os.homedir(), '.vscode/extensions');
  const exts = path.join(base, 'ext');
  fs.mkdirSync(exts);
  const OURS = 'kenichi-morihara.dark-modern-rose-1.0.0';
  for (const name of fs.readdirSync(srcExts)) {
    if (name === OURS || name === 'extensions.json' || name.startsWith('.')) continue;
    fs.symlinkSync(path.join(srcExts, name), path.join(exts, name));
  }
  fs.symlinkSync(theme, path.join(exts, OURS));
  const manifest = path.join(srcExts, 'extensions.json');
  if (fs.existsSync(manifest)) {
    const entries = JSON.parse(fs.readFileSync(manifest, 'utf8')).map((e) => {
      const rel = e.relativeLocation ?? path.basename(e.location?.path ?? '');
      return { ...e, location: { ...e.location, path: path.join(exts, rel), fsPath: path.join(exts, rel) } };
    });
    fs.writeFileSync(path.join(exts, 'extensions.json'), JSON.stringify(entries));
  }
  const user = path.join(base, 'ud/User');
  fs.mkdirSync(user, { recursive: true });
  writeSettings(path.join(base, 'ud'), THEMES[0].label);
  return { base, ws, userData: path.join(base, 'ud'), exts };
}

async function cdp(wsUrl, expression) {
  const sock = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => { sock.onopen = resolve; sock.onerror = reject; });
  const reply = new Promise((resolve) => { sock.onmessage = (e) => resolve(JSON.parse(e.data)); });
  sock.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: { expression, returnByValue: true } }));
  const msg = await reply;
  sock.close();
  return msg.result?.result?.value;
}

const READ_LINES = `(() => {
  const views = [...document.querySelectorAll('.view-lines')].sort((a, b) => b.children.length - a.children.length);
  return [...views[0].querySelectorAll('.view-line')].map((line) =>
    [...line.querySelectorAll('span[class*=mtk]')].map((s) => {
      const [r, g, b] = getComputedStyle(s).color.match(/\\d+/g).map(Number);
      return { text: s.textContent.replace(/\\u00a0/g, ' '), color: '#' + [r, g, b].map((x) => x.toString(16).padStart(2, '0')).join('').toUpperCase() };
    }));
})()`;

function colorOf(lines, needle, word, nth = 0) {
  const hits = lines.filter((toks) => toks.map((t) => t.text).join('').includes(needle));
  const re = new RegExp(`(?<![\\w@$:?!])${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\w?!])`, 'g');
  let seen = 0;
  for (const t of hits[0] ?? []) {
    for (const _ of t.text.matchAll(re)) { if (seen++ === nth) return t.color; }
  }
  return undefined;
}

function check(lines, expectations, palette, prefix) {
  const failures = [];
  for (const [needle, word, role, nth] of expectations) {
    const got = colorOf(lines, needle, word, nth);
    if (got !== palette[role]) failures.push(`${prefix} ${needle} | ${word}${nth ? ` #${nth}` : ''}: got ${got ?? 'missing'} want ${role} ${palette[role]}`);
  }
  return failures;
}

async function waitForRubyLsp(userData, timeoutMs = 300000) {
  const logs = path.join(userData, 'logs');
  for (const end = Date.now() + timeoutMs; Date.now() < end; await sleep(2000)) {
    const found = fs.existsSync(logs) && fs.readdirSync(logs, { recursive: true })
      .filter((f) => String(f).endsWith('Ruby LSP.log'))
      .some((f) => fs.readFileSync(path.join(logs, String(f)), 'utf8').includes('Finished initializing Ruby LSP'));
    if (found) return true;
  }
  return false;
}

function rubyLspLogTail(userData) {
  const logs = path.join(userData, 'logs');
  if (!fs.existsSync(logs)) return '(no logs)';
  const files = fs.readdirSync(logs, { recursive: true }).map(String).filter((f) => f.endsWith('Ruby LSP.log'));
  if (!files.length) return '(no Ruby LSP log: is the ruby-lsp extension installed?)';
  return fs.readFileSync(path.join(logs, files[0]), 'utf8').split('\n').filter((l) => !/^\S+ \S+ \[error\] \(\S+\) \s+from /.test(l)).slice(-25).join('\n');
}

async function main() {
  const { base, ws, userData, exts } = prepareWorkspace();
  const at = (name, line) => `${path.join(ws, name)}:${line}`;
  const app = spawn(BIN, ['--user-data-dir', userData, '--extensions-dir', exts, `--remote-debugging-port=${PORT}`, '--new-window', ws, '-g', at('lineage.rb', 1)],
    { stdio: 'ignore', detached: true });
  const total = THEMES.length * Object.values(EXPECTATIONS).flat().length;
  let failures = ['did not finish'];
  try {
    let page;
    for (let i = 0; i < 60 && !page; i++) {
      await sleep(1000);
      try {
        const targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
        page = targets.find((t) => t.type === 'page' && t.title.includes('lineage.rb'));
      } catch { /* not up yet */ }
    }
    if (!page) throw new Error('VS Code window did not open');
    // Wait for ruby-lsp (the first run may bundle install ruby-lsp itself).
    if (!(await waitForRubyLsp(userData))) {
      throw new Error('ruby-lsp did not finish initializing:\n' + rubyLspLogTail(userData));
    }
    await sleep(5000); // semantic tokens are requested after initialization
    const read = async (name) => {
      const lines = [];
      for (const line of [1, 30]) {
        execFileSync(CLI, ['--user-data-dir', userData, '--extensions-dir', exts, '-r', '-g', at(name, line)]);
        await sleep(1500);
        lines.push(...(await cdp(page.webSocketDebuggerUrl, READ_LINES)) ?? []);
      }
      return lines;
    };
    // tsserver starts lazily on the first TS file: wait until its semantic tokens are painted.
    const settled = (lines) => colorOf(lines, 'const store = new OrderStore', 'OrderStore') === BASE.class;
    for (let i = 0; i < 30 && !settled(await read('component.tsx')); i++) await sleep(2000);
    failures = [];
    for (const theme of THEMES) {
      writeSettings(userData, theme.label);
      await sleep(3000);
      for (const [name, expectations] of Object.entries(EXPECTATIONS)) {
        const lines = await read(name);
        if (process.env.E2E_DUMP) console.error(theme.label, name, JSON.stringify(lines));
        failures.push(...check(lines, expectations, theme.palette, `[${theme.label}] ${name}:`));
      }
    }
  } finally {
    try { process.kill(-app.pid); } catch { /* already gone */ }
    // Electron re-spawns helpers outside the process group: match on the temp dir instead.
    try { execFileSync('pkill', ['-f', base]); } catch { /* none left */ }
    await sleep(2000);
    try { execFileSync('pkill', ['-9', '-f', base]); } catch { /* none left */ }
    await sleep(1000);
    if (process.env.E2E_KEEP) console.error('kept: ' + base); else fs.rmSync(base, { recursive: true, force: true });
  }
  if (failures.length) {
    console.error(`FAILED ${failures.length}/${total}`);
    for (const f of failures) console.error('  ' + f);
    process.exit(1);
  }
  console.log(`OK ${total}/${total}`);
}

await main();
