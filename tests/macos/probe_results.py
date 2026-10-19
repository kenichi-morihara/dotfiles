"""Parse only probe output lines, never commands echoed by ZLE."""
import re

EXPECTED = {
    'corepack', 'brew', 'starship', 'mise', 'deno', 'fzf', 'ghq', 'lua', 'ranger',
    'zeno-completion', 'zeno-ghq-cd', 'history-substring-search-up',
    'history-substring-search-down', 'reload-shell', 'zeno-ready',
    'binding-zeno-ghq-cd', 'binding-zeno-completion', 'binding-reload-shell',
}


def marker(output, name):
    return re.search(rb'(?:^|[\r\n])__DOTFILES_' + name.encode() + rb'__[\r\n]', output) is not None


def checks(output):
    return {name.decode(): status.decode() for name, status in
            re.findall(rb'(?:^|[\r\n])__CHECK_([a-zA-Z0-9_-]+)=(PASS|FAIL)[\r\n]', output)}
