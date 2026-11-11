// Tokenize a file with the same TextMate engine and grammars VS Code uses, and
// print each line's tokens with the colour the Dark Modern Rose theme assigns.
//
// usage: node tokenize.mjs <extension-dir> <root-scope> <file> [theme-file]
//        theme-file is relative to <extension-dir>/themes (default dark-modern-rose.json)
// output: JSON [[{text, color, scopes}], ...] (one array per line)
//
// vscode-textmate / vscode-oniguruma are taken from the installed VS Code app
// (extracted from node_modules.asar into a cache dir), so the result matches the
// editor's TextMate pass. Semantic tokens (ruby-lsp) are not modelled here.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';

const [extDir, rootScope, file, themeFile = 'dark-modern-rose.json'] = process.argv.slice(2);
const APP = process.env.VSCODE_APP || '/Applications/Visual Studio Code.app/Contents/Resources/app';
const EXT_HOME = process.env.VSCODE_EXTENSIONS || path.join(os.homedir(), '.vscode/extensions');

function extractFromAsar(asar, prefix, outDir) {
  const fd = fs.openSync(asar, 'r');
  const head = Buffer.alloc(16);
  fs.readSync(fd, head, 0, 16, 0);
  const headerSize = head.readUInt32LE(4);
  const jsonSize = head.readUInt32LE(12);
  const json = Buffer.alloc(jsonSize);
  fs.readSync(fd, json, 0, jsonSize, 16);
  const header = JSON.parse(json.toString());
  const base = 8 + headerSize;
  const walk = (node, p) => {
    if (node.files) {
      for (const [k, v] of Object.entries(node.files)) walk(v, p ? `${p}/${k}` : k);
      return;
    }
    if (!p.startsWith(prefix) || node.unpacked) return;
    const out = path.join(outDir, p);
    fs.mkdirSync(path.dirname(out), { recursive: true });
    const buf = Buffer.alloc(node.size);
    fs.readSync(fd, buf, 0, node.size, base + Number(node.offset));
    fs.writeFileSync(out, buf);
  };
  walk(header, '');
}

function loadEngine() {
  const version = JSON.parse(fs.readFileSync(path.join(APP, 'package.json'))).version;
  const cache = path.join(os.tmpdir(), `dark-modern-rose-textmate-${version}`);
  const mods = path.join(cache, 'node_modules');
  if (!fs.existsSync(path.join(mods, 'vscode-oniguruma/release/onig.wasm'))) {
    const asar = path.join(APP, 'node_modules.asar');
    extractFromAsar(asar, 'vscode-textmate', mods);
    extractFromAsar(asar, 'vscode-oniguruma', mods);
    fs.copyFileSync(path.join(APP, 'node_modules.asar.unpacked/vscode-oniguruma/release/onig.wasm'),
      path.join(mods, 'vscode-oniguruma/release/onig.wasm'));
  }
  const require = createRequire(path.join(cache, 'index.js'));
  return { tm: require('vscode-textmate'), onig: require('vscode-oniguruma'), wasm: path.join(mods, 'vscode-oniguruma/release/onig.wasm') };
}

function findExtension(prefix) {
  const hit = fs.readdirSync(EXT_HOME).filter((d) => d.startsWith(prefix)).sort().pop();
  return hit ? path.join(EXT_HOME, hit) : null;
}

// Collect grammars the way VS Code does: base grammars by scopeName, injections by injectTo.
function collectGrammars(extensionDirs) {
  const grammars = {};
  const injections = {};
  for (const dir of extensionDirs) {
    const pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json')));
    for (const g of pkg.contributes?.grammars ?? []) {
      grammars[g.scopeName] = path.join(dir, g.path);
      for (const target of g.injectTo ?? []) (injections[target] ??= []).push(g.scopeName);
    }
  }
  return { grammars, injections };
}

const { tm, onig, wasm } = loadEngine();
await onig.loadWASM(fs.readFileSync(wasm).buffer);

const builtinHtml = path.join(APP, 'extensions/html');
const dirs = [path.join(APP, 'extensions/ruby'), builtinHtml, path.join(APP, 'extensions/typescript-basics'), path.join(APP, 'extensions/javascript'),
  findExtension('shopify.ruby-lsp-'), findExtension('sarahridge.vscode-rails-syntax-'), extDir].filter(Boolean);
const { grammars, injections } = collectGrammars(dirs);
// Resolve `include` the way VS Code does: the included theme's rules first, own rules appended.
function loadTheme(file) {
  const own = JSON.parse(fs.readFileSync(file));
  if (!own.include) return own;
  const base = loadTheme(path.join(path.dirname(file), own.include));
  return { ...base, ...own, colors: { ...base.colors, ...own.colors }, tokenColors: [...base.tokenColors, ...(own.tokenColors ?? [])] };
}
const theme = loadTheme(path.join(extDir, 'themes', themeFile));

const registry = new tm.Registry({
  onigLib: Promise.resolve({ createOnigScanner: (s) => new onig.OnigScanner(s), createOnigString: (s) => new onig.OnigString(s) }),
  loadGrammar: async (scope) => (grammars[scope] ? tm.parseRawGrammar(fs.readFileSync(grammars[scope], 'utf8'), grammars[scope]) : null),
  getInjections: (scope) => injections[scope],
  theme: { settings: [{ settings: { foreground: theme.colors['editor.foreground'] } }, ...theme.tokenColors] },
});
const colorMap = registry.getColorMap();
const grammar = await registry.loadGrammar(rootScope);

const result = [];
let state = tm.INITIAL;
for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
  const scoped = grammar.tokenizeLine(line, state);
  const binary = grammar.tokenizeLine2(line, state);
  state = scoped.ruleStack;
  result.push(scoped.tokens.map((t) => {
    let color;
    for (let i = 0; i < binary.tokens.length; i += 2) {
      if (binary.tokens[i] <= t.startIndex) color = colorMap[(binary.tokens[i + 1] >>> 15) & 0x1ff];
    }
    return { text: line.slice(t.startIndex, t.endIndex), color: color.toUpperCase(), scopes: t.scopes };
  }));
}
process.stdout.write(JSON.stringify(result));
