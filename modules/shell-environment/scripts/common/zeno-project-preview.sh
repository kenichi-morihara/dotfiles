#!/bin/bash
# fzf passes an absolute repository path as one argument, including spaces.
set -euo pipefail
cd -- "$1"
for readme in README.md README.markdown README.rst README.txt README readme.md; do
    if [ -f "$readme" ]; then
        if command -v bat >/dev/null 2>&1; then
            exec bat --color=always --paging=never --style=plain --theme=Dracula --line-range=:240 -- "$readme"
        fi
        exec head -n 240 -- "$readme"
    fi
done
if command -v eza >/dev/null 2>&1; then
    exec eza --tree --level=2 --color=always -- .
fi
ls -la
