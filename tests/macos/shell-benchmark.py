#!/usr/bin/env python3
"""Measure cold and warm interactive login zsh startup in an isolated HOME."""
import argparse
import atexit
import json
import math
import os
import platform
import signal
from pathlib import Path
import pty
import select
import statistics
import subprocess
import termios
import time

ROOT = Path(__file__).resolve().parents[2]
MARKER = b"__DOTFILES_SHELL_READY__"


def percentile(values, fraction):
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return round(ordered[min(len(ordered) - 1, index)], 3)


def run_shell(env, home, timeout):
    master, slave = pty.openpty()
    attrs = termios.tcgetattr(slave)
    attrs[3] &= ~termios.ECHO
    termios.tcsetattr(slave, termios.TCSANOW, attrs)
    started = time.monotonic()
    proc = subprocess.Popen(['/bin/zsh', '-il'],
                            env=env, cwd=home, stdin=slave, stdout=slave, stderr=slave,
                            start_new_session=True)
    os.close(slave)
    os.write(master, b"print '__DOTFILES_SHELL_READY__'\n")
    output = b''
    try:
        while time.monotonic() - started < timeout:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                chunk = os.read(master, 65536)
                if not chunk:
                    break
                output += chunk
                if MARKER in output:
                    elapsed = time.monotonic() - started
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=5)
                    return round(elapsed, 3), 0
            if proc.poll() is not None:
                break
        raise TimeoutError(f"zsh did not print startup marker within {timeout}s: {output[-1000:]!r}")
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
        os.close(master)


def cleanup_plugin_servers(home):
    """Stop zeno's detached Deno server processes created for this test HOME."""
    listing = subprocess.run(['ps', '-Ao', 'pid=,command='], text=True,
                             capture_output=True, check=False).stdout
    for line in listing.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) != 2 or str(home) not in fields[1] or 'src/server.ts' not in fields[1]:
            continue
        try:
            os.kill(int(fields[0]), signal.SIGTERM)
        except (ProcessLookupError, ValueError):
            pass


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True, help='new output directory')
parser.add_argument('--warm-runs', type=int, default=10)
parser.add_argument('--timeout', type=int, default=120)
args = parser.parse_args()
if args.warm_runs < 1:
    parser.error('--warm-runs must be at least 1')
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
home = out / 'home'
home.mkdir()
atexit.register(cleanup_plugin_servers, home)
env = {'HOME': str(home), 'ZDOTDIR': str(home), 'USER': os.environ.get('USER', 'admin'),
       'LOGNAME': os.environ.get('USER', 'admin'), 'SHELL': '/bin/zsh', 'TERM': 'xterm-256color',
       'LANG': 'en_US.UTF-8', 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
       'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_CACHE_HOME': str(home / '.cache'),
       'XDG_DATA_HOME': str(home / '.local/share')}
with (out / 'links.log').open('w') as log:
    subprocess.run(['/bin/bash', str(ROOT / '.bin/link.sh')], env=env, check=True,
                   stdout=log, stderr=subprocess.STDOUT)
(home / '.zprofile').write_text('if [[ -x /opt/homebrew/bin/brew ]]; then\n'
                               '  eval "$(/opt/homebrew/bin/brew shellenv)"\n'
                               'elif [[ -x /usr/local/bin/brew ]]; then\n'
                               '  eval "$(/usr/local/bin/brew shellenv)"\nfi\n')
cold, code = run_shell(env, home, args.timeout)
if code:
    raise SystemExit(f'cold shell exited with status {code}')
warm = []
for _ in range(args.warm_runs):
    elapsed, code = run_shell(env, home, args.timeout)
    if code:
        raise SystemExit(f'warm shell exited with status {code}')
    warm.append(elapsed)
result = {'cold_startup_seconds': cold, 'warm_runs_seconds': warm,
          'warm_median_seconds': round(statistics.median(warm), 3),
          'warm_p95_seconds': percentile(warm, .95), 'macos_version': platform.mac_ver()[0],
          'architecture': platform.machine(), 'warm_run_count': args.warm_runs,
          'scope': 'isolated HOME; PTY interactive login zsh prompt ready; cold first shell plus repeated warm shells; shared host Homebrew'}
(out / 'benchmark.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
