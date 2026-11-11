#!/usr/bin/env python3
"""Resolve profiles and run explicit, repeatable workstation setup (Python >=3.11)."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
try:
    import tomllib
except ImportError:
    sys.exit('profile 操作には Python 3.11 以上が必要です。Python を導入して PYTHON=/path/to/python3 を指定してください。')

ROOT = Path(__file__).resolve().parents[2]
PERSONAL = 'github.com/kenichi-morihara/'


def selection_path():
    return Path(os.environ.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')) / 'dotfiles/profile'


def resolve(name=None):
    selected = selection_path()
    name = name or (selected.read_text().strip() if selected.exists() else '')
    if not name:
        raise ValueError('先に make profile-select NAME=personal または NAME=work/<端末ID> を実行してください')
    if not re.fullmatch(r'personal|work(?:/[a-zA-Z0-9][a-zA-Z0-9_-]*)?', name):
        raise ValueError(f'不正な profile: {name}')
    files = ['common', name.split('/')[0]]
    if '/' in name:
        if name == 'work/example':
            raise ValueError('example を端末IDにコピーしてください')
        files.append(name)
    config = {}
    for entry in files:
        with (ROOT / 'profiles' / (entry + '.toml')).open('rb') as source:
            merge(config, tomllib.load(source))
    allowed = {'package_profile', 'keyboard_layout', 'packages', 'casks', 'repos', 'knowledge_features'}
    if set(config) - allowed:
        raise ValueError('未知の profile 設定: ' + ', '.join(set(config) - allowed))
    if config['package_profile'] not in ('core', 'full') or config['keyboard_layout'] not in ('jis', 'us'):
        raise ValueError('package_profile は core/full、keyboard_layout は jis/us を指定してください')
    for key in ('packages', 'casks', 'repos', 'knowledge_features'):
        if not isinstance(config[key], list) or any(not isinstance(x, str) for x in config[key]):
            raise ValueError(f'{key} は文字列のリストで指定してください')
    for repo in config['repos']:
        if not re.fullmatch(r'[\w.-]+/[\w.-]+/[\w.-]+', repo) or any(x in ('.', '..') for x in repo.split('/')):
            raise ValueError(f'不正な repo: {repo}')
    for package in config['packages'] + config['casks']:
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9@+._/-]*', package):
            raise ValueError(f'不正な package: {package}')
    if set(config['knowledge_features']) - {'capture', 'ledger'}:
        raise ValueError('knowledge_features は capture/ledger のみです')
    return dict(config, name=name)


def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        raise ValueError('入力が中断されました')


def create_machine(machine):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', machine) or machine == 'example':
        raise ValueError(f'端末IDには英数字・ハイフン・アンダースコアを使ってください: {machine}')
    target = ROOT / 'profiles/work' / (machine + '.toml')
    if not target.exists():
        shutil.copyfile(ROOT / 'profiles/work/example.toml', target)
        print(f'作成: {target.relative_to(ROOT)}（追加パッケージ等は後で編集できます）')
    return 'work/' + machine


def choose_interactively():
    machines = sorted(p.stem for p in (ROOT / 'profiles/work').glob('*.toml') if p.stem != 'example')
    options = [('personal', '個人用'), ('work', '会社用（端末別の設定なし）')]
    options += [('work/' + m, '会社用の端末設定') for m in machines]
    print('profile を選んでください:')
    for number, (name, label) in enumerate(options, 1):
        print(f'  {number}) {name:<20} {label}')
    print(f'  {len(options) + 1}) 会社用の端末設定を新しく作る')
    answer = ask('番号: ')
    if not answer.isdigit() or not 1 <= int(answer) <= len(options) + 1:
        raise ValueError(f'番号で選んでください: {answer}')
    if int(answer) <= len(options):
        return options[int(answer) - 1][0]
    return create_machine(ask('端末ID（例: primenumber-mac）: '))


def interactive():
    return sys.stdin.isatty() and sys.stdout.isatty()


def merge(target, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge(target[key], value)
        else:
            target[key] = value


def run(args, cwd=ROOT):
    print('+ ' + shlex.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)


def repo_checkout(repo):
    paths = subprocess.check_output(['ghq', 'list', '--full-path'], text=True).splitlines()
    matches = [Path(p) for p in paths if p.rstrip('/').endswith('/' + repo)]
    if len(matches) > 1:
        raise ValueError(f'{repo}: checkout が複数あります。ghq の設定を確認してください')
    if matches:
        return matches[0]
    return None


def prepare_repo(repo, features):
    checkout = repo_checkout(repo)
    if checkout is None:
        run(['ghq', 'get', repo])
        checkout = repo_checkout(repo)
        if checkout is None:
            raise ValueError(f'{repo}: ghq get 後に checkout が見つかりません')
    if repo == PERSONAL + 'personal-ops':
        run(['mise', 'exec', '--', 'npm', 'ci'], checkout / 'ai-tasks')
        if not shutil.which('gmailctl'):
            run(['brew', 'install', 'gmailctl'] if platform.system() == 'Darwin' else
                ['mise', 'exec', '--', 'go', 'install', 'github.com/mbrt/gmailctl/cmd/gmailctl@v0.13.0'])
    elif repo == PERSONAL + 'personal-knowledge':
        python = checkout / '.venv/bin/python'
        if not python.exists():
            run([sys.executable, '-m', 'venv', '.venv'], checkout)
        run([python, '-m', 'pip', 'install', '-r', 'requirements-mcp.txt'], checkout)
        if 'capture' in features:
            run([python, '-m', 'pip', 'install', '-r', 'requirements-capture.txt'], checkout)
        if 'ledger' in features:
            run(['make', 'ledger-setup', 'PYTHON=' + sys.executable], checkout)
    elif repo == PERSONAL + 'mac-security-audit':
        run([sys.executable, '--version'], checkout)


def execute(config, action, package_override=None, check=False):
    if action in ('setup', 'packages'):
        if platform.system() != 'Darwin':
            raise ValueError('profile によるパッケージ導入は macOS 対応です。Linux/Windows は既存のOS別手順を使用してください')
        run(['bash', 'scripts/macos/brew.sh', '--profile', package_override or config['package_profile']] + (['check'] if check else []))
        # Temporary Brewfile keeps profile additions out of the shared auto-dump.
        with tempfile.TemporaryDirectory() as tmp:
            brewfile = Path(tmp) / 'Brewfile'
            brewfile.write_text(''.join(f'{kind} {json.dumps(p)}\n' for key, kind in [('packages', 'brew'), ('casks', 'cask')] for p in config[key]))
            if config['packages'] or config['casks']:
                run(['brew', 'bundle', '--file=' + str(brewfile)] + (['check'] if check else []))
    if action == 'setup':
        run(['make', 'init'])
        run(['make', 'apply'])
        run(['make', 'runtimes'])
    if action in ('setup', 'repos'):
        for repo in config['repos']:
            print(f'準備: {repo}', flush=True)
            prepare_repo(repo, config['knowledge_features'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['select', 'show', 'plan', 'setup', 'packages', 'repos'])
    parser.add_argument('--name')
    parser.add_argument('--package-profile', choices=['core', 'full'])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'select' and not args.name:
            if not interactive():
                raise ValueError('NAME を指定してください（例: NAME=work）')
            args.name = choose_interactively()
        if args.action == 'select' and args.name.startswith('work/'):
            machine = args.name.split('/', 1)[1]
            if machine != 'example' and not (ROOT / 'profiles/work' / (machine + '.toml')).exists():
                if interactive() and ask(f'profiles/work/{machine}.toml がありません。作成しますか？ [Y/n] ').lower() in ('', 'y', 'yes'):
                    create_machine(machine)
                else:
                    raise ValueError(f'profiles/work/{machine}.toml がありません。make profile-select で対話的に作成するか、NAME=work を使ってください')
        if args.name and args.action != 'select':
            raise ValueError('--name は select のみで使用できます。先に profile を選択してください')
        config = resolve(args.name)
        if args.action == 'select':
            target = selection_path()
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix('.tmp')
            temporary.write_text(config['name'] + '\n')
            temporary.replace(target)
            print('選択: ' + config['name'] + '（適用は make setup）')
        elif args.action in ('show', 'plan'):
            print(json.dumps(config, ensure_ascii=False, indent=2))
            if args.action == 'plan':
                print('順序: Homebrew → make init → make apply → mise install → ghq 取得 → repo 依存導入')
                for repo in config['repos']:
                    preparation = {
                        PERSONAL + 'personal-ops': 'mise exec -- npm ci / gmailctl',
                        PERSONAL + 'personal-knowledge': '.venv / requirements-mcp.txt; optional=' + ','.join(config['knowledge_features']),
                        PERSONAL + 'mac-security-audit': 'Python確認',
                    }.get(repo, 'checkoutのみ')
                    print(f'{repo}: {preparation}')
                print('既存checkoutを再利用。認証・サービス起動・DB初期化・外部への適用は実行しません。')
        else:
            execute(config, args.action, args.package_profile, args.check)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'profile 処理を停止: {exc}\n修正後、同じ make コマンドを再実行してください。', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
