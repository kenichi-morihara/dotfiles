#!/usr/bin/env python3
"""Launch real interactive login zsh with a fresh HOME and a PTY."""
import argparse
import errno
import fcntl
import json
import os
import platform
from pathlib import Path
import pty
import select
import subprocess
import struct
import signal
import termios
import time

from probe_results import EXPECTED, checks as parse_checks, marker

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / '.validation/shell')
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
home = out / 'home'
if home.exists():
    parser.error('HOME already exists; use a new --output directory for a first-run test')
home.mkdir()
env = {'HOME': str(home), 'ZDOTDIR': str(home), 'USER': os.environ.get('USER', 'admin'),
       'LOGNAME': os.environ.get('USER', 'admin'), 'SHELL': '/bin/zsh', 'TERM': 'xterm-256color',
       'LANG': 'en_US.UTF-8', 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
       'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_CACHE_HOME': str(home / '.cache'),
       'XDG_DATA_HOME': str(home / '.local/share')}
with (out / 'links.log').open('w') as log:
    subprocess.run(['/bin/bash', str(ROOT / 'scripts/link.sh')], env=env, check=True,
                   stdout=log, stderr=subprocess.STDOUT)
# Follow the documented Homebrew login-shell setup, without inheriting host PATH.
(home / '.zprofile').write_text('if [[ -x /opt/homebrew/bin/brew ]]; then\n'
                              '  eval "$(/opt/homebrew/bin/brew shellenv)"\n'
                              'elif [[ -x /usr/local/bin/brew ]]; then\n'
                              '  eval "$(/usr/local/bin/brew shellenv)"\nfi\n')
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 120, 0, 0))
attrs = termios.tcgetattr(slave)
attrs[3] &= ~termios.ECHO
termios.tcsetattr(slave, termios.TCSANOW, attrs)
proc = subprocess.Popen(['/bin/zsh', '-il'], env=env, cwd=home,
                        stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
os.close(slave)
start = time.monotonic()
ready = False
sent = False
finished = False
checks = {}
buffer = b''
next_prompt = 0
os.write(master, b"print '__DOTFILES_'READY__\n")
try:
    with (out / 'shell.log').open('wb') as log:
        while time.monotonic() - start < 240:
            if select.select([master], [], [], 0.2)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                log.write(chunk)
                log.flush()
                buffer += chunk
                if not ready and marker(buffer, 'READY'):
                    ready = time.monotonic()
            if ready and not sent and time.monotonic() >= next_prompt:
                os.write(master, b'\n')
                next_prompt = time.monotonic() + 1
            if ready and not sent and time.monotonic() - ready > 15:
                command = '''
for tool in brew starship mise deno fzf ghq lua ranger corepack; do
  if whence -p "$tool" >/dev/null; then print "__CHECK_${tool}=PASS"; else print "__CHECK_${tool}=FAIL"; fi
done
for widget in zeno-completion zeno-ghq-cd history-substring-search-up history-substring-search-down reload-shell; do
  if (( ${+widgets[$widget]} )); then print "__CHECK_${widget}=PASS"; else print "__CHECK_${widget}=FAIL"; fi
done
if [[ -n $ZENO_LOADED || -n $ZENO_BOOTSTRAPPED ]]; then print __CHECK_zeno-ready=PASS; else print __CHECK_zeno-ready=FAIL; fi
for pair in '^g:zeno-ghq-cd' '^i:zeno-completion' '^r:reload-shell'; do
  key=${pair%%:*}; expected=${pair#*:}
  if [[ $(bindkey "$key") == *" $expected" ]]; then print "__CHECK_binding-${expected}=PASS"; else print "__CHECK_binding-${expected}=FAIL"; fi
done
print '__DOTFILES_'DONE__
'''
                os.write(master, command.encode())
                sent = True
            if not finished and marker(buffer, 'DONE'):
                os.write(master, b'exit\n')
                finished = True
            if proc.poll() is not None:
                break
finally:
    if proc.poll() is None:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
    os.close(master)
checks = parse_checks(buffer)
result = {'passed': set(checks) == EXPECTED and all(v == 'PASS' for v in checks.values())
          and marker(buffer, 'DONE') and proc.returncode == 0, 'checks': checks,
          'duration_seconds': round(time.monotonic() - start, 1), 'shell_exit_code': proc.returncode,
          'scope': 'fresh HOME; shared host Homebrew and macOS'}
revisions = {}
plugin_root = home / '.local/share/zinit/plugins'
if plugin_root.exists():
    for plugin in sorted(plugin_root.iterdir()):
        if (plugin / '.git').is_dir():
            revision = subprocess.run(['/usr/bin/git', '-C', str(plugin), 'rev-parse', 'HEAD'],
                                      env=env, text=True, capture_output=True)
            if revision.returncode == 0:
                revisions[plugin.name] = revision.stdout.strip()
result['plugin_revisions'] = revisions
result['macos_version'] = platform.mac_ver()[0]
result['architecture'] = platform.machine()
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['passed'] else 1)
