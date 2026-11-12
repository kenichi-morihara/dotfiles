#!/usr/bin/env python3
"""Record a setup run and safely undo its chezmoi file changes."""
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FILE_ACTIONS = {'setup', 'init', 'apply', 'apply-files'}
APP_ACTIONS = {'setup', 'apply', 'apply-apps'}
INSTALL_ACTIONS = {'macos-init', 'setup', 'packages', 'runtimes', 'repos'}
ACTIONS = FILE_ACTIONS | APP_ACTIONS | INSTALL_ACTIONS | {'apply-system', 'sudo-touchid', 'shell-setup'}
APP_DOMAINS = ('com.knollsoft.Rectangle', 'com.googlecode.iterm2', 'com.apple.HIToolbox')
SYSTEM_DOMAINS = (
    'NSGlobalDomain', 'com.apple.inputmethod.Kotoeri', 'com.apple.dock',
    'com.apple.lookup.shared', 'com.apple.assistant.support', 'com.googlecode.iterm2',
    'com.apple.symbolichotkeys',
)


def target(home, name):
    relative = Path(name)
    if relative.is_absolute() or not relative.parts or '..' in relative.parts:
        raise ValueError(f'無効な対象パス: {name}')
    path = home / relative
    for parent in reversed(relative.parents):
        if parent != Path('.'):
            ancestor = home / parent
            if ancestor.is_symlink() or (ancestor.exists() and not ancestor.is_dir()):
                raise ValueError(f'親ディレクトリを安全にたどれません: {ancestor}')
    return path


def file_state(path):
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(mode):
        return {'kind': 'link', 'target': os.readlink(path)}
    if stat.S_ISREG(mode):
        return {'kind': 'file', 'mode': stat.S_IMODE(mode),
                'data': base64.b64encode(path.read_bytes()).decode('ascii')}
    if stat.S_ISDIR(mode):
        return {'kind': 'directory', 'mode': stat.S_IMODE(mode)}
    raise ValueError(f'未対応のファイル種別: {path}')


def managed(home, chezmoi):
    command = [chezmoi, '--source', str(ROOT), '--destination', str(home),
               '--refresh-externals=never', 'managed', '--include=dirs,files,symlinks,remove',
               '--nul-path-separator']
    names = set(os.fsdecode(subprocess.check_output(command)).strip('\0').split('\0')) - {''}
    names.update(str(p) for name in list(names) for p in Path(name).parents if p != Path('.'))
    return names


def capture_files(home, names):
    return {name: file_state(target(home, name)) for name in sorted(names)}


def native_state(home, action):
    """Keep reference data for selective manual restore, including tool errors."""
    commands = {}
    if action in INSTALL_ACTIONS:
        commands.update({
            'brew-formulae': ['brew', 'list', '--formula', '--versions'],
            'brew-casks': ['brew', 'list', '--cask', '--versions'],
            'mise': ['mise', 'ls', '--installed', '--json'],
            'vscode': ['code', '--list-extensions', '--show-versions'],
            'ghq': ['ghq', 'list', '--full-path'],
            'npm': ['npm', 'ls', '--global', '--depth=0', '--json'],
        })
    if sys.platform == 'darwin':
        domains = set(APP_DOMAINS if action in APP_ACTIONS else ())
        if action == 'apply-system':
            domains.update(SYSTEM_DOMAINS)
            commands.update({
                'control-center': ['defaults', '-currentHost', 'export', 'com.apple.controlcenter', '-'],
                'power': ['pmset', '-g', 'custom'],
                'spotlight': ['mdutil', '-a', '-s'],
            })
        commands.update({domain: ['defaults', 'export', domain, '-'] for domain in domains})
    state = {}
    for label, command in sorted(commands.items()):
        if not shutil.which(command[0]):
            state[label] = {'unavailable': command[0]}
            continue
        result = subprocess.run(command, capture_output=True, text=True, errors='replace')
        state[label] = {'status': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    if action == 'shell-setup':
        state['login-shell'] = pwd.getpwuid(os.getuid()).pw_shell
        state['etc-shells'] = file_state(Path('/etc/shells'))
    if action == 'sudo-touchid':
        state['sudo-local'] = file_state(Path('/etc/pam.d/sudo_local'))
    if action in APP_ACTIONS:
        state['app-backups'] = app_backups(home)
    return state


def app_backups(home):
    return {
        app: sorted(str(p.relative_to(home)) for p in
                    (home / 'Library/Application Support' / app / 'dotfiles-backups').glob(pattern)
                    if p.is_file() and not p.is_symlink())
        for app, pattern in [('Rectangle', 'preferences.*'), ('Nani', 'preferences.*.json'),
                             ('iTerm2', 'backup.*.plist')]
    }


def write_manifest(path, record):
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


@contextmanager
def locked(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError(f'記録先には本人専用のディレクトリが必要です: {directory}')
    with (directory / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def track(home, directory, args):
    if args.action in {'apply-system', 'sudo-touchid'} and sys.platform != 'darwin':
        raise ValueError('この操作は macOS 専用です')
    names = managed(home, args.chezmoi) if args.action in FILE_ACTIONS else set()
    before = capture_files(home, names)
    reference_before = native_state(home, args.action)
    if args.action == 'apply-system':
        for name in ('power', 'spotlight'):
            saved = reference_before[name]
            if saved.get('status') != 0 or not saved.get('stdout', '').strip():
                raise ValueError(f'適用前の状態を取得できません: {name}')
    session = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = directory / (session + '.json')
    record = {'home': str(home), 'action': args.action, 'before': before,
              'reference_before': reference_before}
    write_manifest(path, record)
    print(f'復元記録: {path}', flush=True)
    command = [args.make, args.action, 'CHEZMOI=' + args.chezmoi, 'PYTHON=' + sys.executable]
    if args.profile:
        command.append('PROFILE=' + args.profile)
    try:
        result = subprocess.run(command, cwd=ROOT)
        record['exit_status'] = result.returncode
        return result.returncode
    finally:
        record['after'] = capture_files(home, names)
        write_manifest(path, record)
        record['reference_after'] = native_state(home, args.action)
        write_manifest(path, record)


def restore_file(path, desired, current):
    if desired is None:
        if current['kind'] == 'directory':
            path.rmdir()
        else:
            path.unlink()
    elif desired['kind'] == 'directory':
        if current is None:
            # Keep it writable until its children are restored; the caller
            # applies the recorded mode afterwards.
            path.mkdir(mode=desired['mode'] | 0o700)
        elif current['kind'] != 'directory':
            raise ValueError(f'ディレクトリへの変換は手動で復元してください: {path}')
        return desired['mode']
    else:
        with tempfile.TemporaryDirectory(dir=path.parent) as directory:
            temp = Path(directory) / 'restore'
            if desired['kind'] == 'link':
                temp.symlink_to(desired['target'])
            else:
                temp.write_bytes(base64.b64decode(desired['data'], validate=True))
                temp.chmod(desired['mode'])
            temp.replace(path)


def rollback(home, record, apply=False, selected=None, chezmoi='chezmoi'):
    if record['home'] != str(home) or 'after' not in record:
        raise ValueError('別の HOME または適用後の状態を記録できなかった実行です')
    before, after = record['before'], record['after']
    if selected and selected not in before:
        raise ValueError(f'復元記録にないパス: {selected}')
    changes = [name for name in before if before[name] != after[name] and
               (selected is None or name == selected)]
    # Recreate parents before children and remove newly created directories last.
    changes.sort(key=lambda name: (before[name] is None,
                                   -len(Path(name).parts) if before[name] is None else len(Path(name).parts),
                                   name))
    failed = False
    modes = []
    restored = []
    for name in changes:
        try:
            path = target(home, name)
            current = file_state(path)
            if current == before[name]:
                print(f'復元済み  {name}')
                restored.append(name)
            elif current != after[name]:
                print(f'競合      {name}')
                failed = True
            else:
                if current and current['kind'] == 'directory' and before[name] is None:
                    children = {str(p.relative_to(home)) for p in path.iterdir()}
                    if children - set(changes):
                        raise ValueError('記録対象外のファイルが入っています')
                print(f'{"削除" if before[name] is None else "復元"}      {name}')
                if apply:
                    mode = restore_file(path, before[name], current)
                    restored.append(name)
                    if mode is not None:
                        modes.append((name, path, mode))
        except (OSError, ValueError) as error:
            print(f'保留      {name}: {error}', file=sys.stderr)
            failed = True
    # Directory modes last and deepest first, so a read-only directory does not
    # block restoring its own children.
    for name, path, mode in sorted(modes, key=lambda item: -len(Path(item[0]).parts)):
        try:
            path.chmod(mode)
        except OSError as error:
            print(f'保留      {name}: {error}', file=sys.stderr)
            failed = True
    if apply:
        forget(home, restored, chezmoi)
    return int(failed)


def forget(home, names, chezmoi):
    """Drop chezmoi's last-written state so the next apply does not treat
    restored targets as manual edits (prompting, or failing without a TTY)."""
    # chezmoi keys entries by its destination path, which follows $HOME as given.
    roots = dict.fromkeys([home, Path(os.environ.get('HOME') or home)])
    for name in names:
        for root in roots:
            command = [chezmoi, 'state', 'delete', '--bucket=entryState', f'--key={root / name}']
            try:
                result = subprocess.run(command, capture_output=True, text=True)
            except OSError as error:
                result = None
                reason = str(error)
            else:
                reason = result.stderr.strip()
            if result is None or result.returncode != 0:
                print(f'注意      chezmoi の記録を更新できません: {name}（次回の適用で確認が表示されます）{reason}')
                break


def inventory_entries(name, output):
    entries = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        if name == 'ghq':
            key = line
        elif name == 'vscode':
            key = line.split('@', 1)[0]
        else:
            key = line.split()[0]
        entries[key] = line
    return entries


def report(home, record):
    status = rollback(home, record)
    after = record.get('reference_after', {})
    for name, before in record.get('reference_before', {}).items():
        if name not in after or before != after[name]:
            print(f'確認対象  {name}（設定値・導入状況の記録を確認）')
    for name in ('brew-formulae', 'brew-casks', 'vscode', 'ghq'):
        before = record.get('reference_before', {}).get(name, {})
        current = after.get(name, {})
        if before.get('status') != 0 or current.get('status') != 0:
            continue
        old = inventory_entries(name, before['stdout'])
        for key, entry in inventory_entries(name, current['stdout']).items():
            if key not in old:
                print(f'追加候補  {name}: {entry}')
    return status


def legacy(home, chezmoi):
    for name in sorted(managed(home, chezmoi)):
        path = target(home, name)
        active = file_state(path)
        for backup in sorted(path.parent.glob(path.name + '.backup*')):
            suffix = backup.name.removeprefix(path.name + '.backup')
            if suffix and not (suffix.startswith('.') and suffix[1:].isdigit()):
                continue
            saved = file_state(backup)
            if not saved or saved['kind'] == 'directory':
                continue
            same = '現行と同じ' if active == saved else '復元元の確認が必要'
            print(f'{same}  {backup.relative_to(home)}')
    for app, paths in app_backups(home).items():
        for path in paths:
            print(f'確認対象  {app}: {path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['track', 'legacy', 'plan', 'restore'])
    parser.add_argument('--action', choices=sorted(ACTIONS))
    parser.add_argument('--run', help='track が表示した実行 ID（.json を除く）')
    parser.add_argument('--target', help='復元する単一の HOME 相対パス')
    parser.add_argument('--chezmoi', default='chezmoi')
    parser.add_argument('--make', default='make')
    parser.add_argument('--profile')
    args = parser.parse_args()
    home = Path.home().resolve()
    try:
        if args.command == 'legacy':
            legacy(home, args.chezmoi)
            return 0
        directory = target(home, '.local/state/dotfiles/rollback')
        if args.command == 'track':
            if not args.action:
                parser.error('track には --action が必要です')
            with locked(directory):
                return track(home, directory, args)
        if not args.run or not args.run.isascii() or not args.run.replace('T', '').replace('Z', '').isdigit():
            parser.error('track が表示した --run を指定してください')
        path = directory / (args.run + '.json')
        if args.command == 'plan':
            return report(home, json.loads(path.read_text()))
        with locked(directory):
            return rollback(home, json.loads(path.read_text()), apply=True, selected=args.target or None,
                            chezmoi=args.chezmoi)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'rollback: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
