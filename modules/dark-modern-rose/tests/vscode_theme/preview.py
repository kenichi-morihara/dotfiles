#!/usr/bin/env python3
"""Render files in the terminal with Dark Modern Rose colours, without opening VS Code.

Uses tokenize.mjs (VS Code's own vscode-textmate engine + the same grammars), so the
colours match the editor's TextMate pass. Semantic tokens (ruby-lsp) are not applied.

usage: preview.py [-w] [-s] [FILE ...]
  -w  watch: re-render whenever the file, the theme or the grammars change
  -s  show scopes of each token (to find out which rule to edit)
  FILE defaults to every sample in the extension's samples/ directory.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / 'home/dot_vscode/extensions/kenichi-morihara.dark-modern-rose-1.0.0'
TOKENIZE = ROOT / 'tests/vscode_theme/tokenize.mjs'
SCOPES = {'.rb': 'source.ruby', '.erb': 'text.html.erb', '.ts': 'source.ts', '.tsx': 'source.tsx',
          '.js': 'source.js', '.jsx': 'source.js.jsx', '.html': 'text.html.basic'}
BG = '#1F1F1F'


def ansi(hex_color, bg=False):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f'\x1b[{48 if bg else 38};2;{r};{g};{b}m'


def render(path, show_scopes):
    scope = SCOPES.get(path.suffix)
    if not scope:
        return f'{path}: unknown extension\n'
    out = subprocess.run(['node', str(TOKENIZE), str(EXT), scope, str(path)], capture_output=True, text=True)
    if out.returncode:
        return out.stderr
    buf = [f'\x1b[1m── {path.name} ({scope})\x1b[0m\n']
    for n, line in enumerate(json.loads(out.stdout), 1):
        buf.append(f'\x1b[90m{n:4} \x1b[0m{ansi(BG, True)}')
        buf.extend(f'{ansi(t["color"])}{t["text"]}' for t in line)
        buf.append('\x1b[K\x1b[0m\n')
        if show_scopes:
            for t in line:
                if t['text'].strip():
                    buf.append(f'       {ansi(t["color"])}{t["text"]!r:24}\x1b[0m {t["color"]} {" ".join(t["scopes"][1:])}\n')
    return ''.join(buf)


def watched(files):
    deps = [*files, *(EXT / 'themes').glob('*.json'), *(EXT / 'syntaxes').glob('*.json'), EXT / 'package.json']
    return tuple(p.stat().st_mtime for p in deps if p.exists())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-w', '--watch', action='store_true')
    ap.add_argument('-s', '--scopes', action='store_true')
    ap.add_argument('files', nargs='*', type=Path)
    args = ap.parse_args()
    # Watching only makes sense in a real terminal (not e.g. Claude Code's `!` or a pipe).
    args.watch = args.watch and sys.stdout.isatty()
    files = [f.resolve() for f in args.files] or sorted((EXT / 'samples').iterdir())
    last = None
    while True:
        stamp = watched(files)
        if stamp != last:
            last = stamp
            text = ''.join(render(f, args.scopes) for f in files)
            if args.watch:
                text = '\x1b[2J\x1b[H' + text + f'\x1b[90m(watching, {time.strftime("%H:%M:%S")})\x1b[0m\n'
            sys.stdout.write(text)
            sys.stdout.flush()
        if not args.watch:
            return
        time.sleep(0.3)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
