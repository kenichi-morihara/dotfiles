#!/usr/bin/env python3
"""Measure cold and warm interactive login zsh startup in an isolated HOME."""
import argparse
import atexit
import json
import errno
import fcntl
import math
import os
import platform
import signal
from pathlib import Path
import pty
import select
import shlex
import statistics
import struct
import subprocess
import termios
import time

from probe_results import checks, marker

ROOT = Path(__file__).resolve().parents[2]
RELOAD_CHECKS = {f"reload-{name}" for name in ("path", "fpath", "hooks", "plugins", "server", "bindings")}


def percentile(values, fraction):
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return round(ordered[min(len(ordered) - 1, index)], 3)


def server_pids(home):
    listing = subprocess.run(['ps', '-Ao', 'pid=,command='], text=True,
                             capture_output=True, check=True).stdout
    return sorted(int(fields[0]) for line in listing.splitlines()
                  if len(fields := line.strip().split(None, 1)) == 2
                  and str(home) in fields[1] and 'src/server.ts' in fields[1])


def cleanup_plugin_servers(home):
    for pid in server_pids(home):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def run_shell(env, home, timeout, logfile):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 120, 0, 0))
    attrs = termios.tcgetattr(slave)
    attrs[3] &= ~termios.ECHO
    termios.tcsetattr(slave, termios.TCSANOW, attrs)
    started = time.monotonic()
    proc = subprocess.Popen(['/bin/zsh', '-il'], env=env, cwd=home,
                            stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
    os.close(slave)
    output = b''
    prompt = features = None
    command_sent = False
    probe_inflight = False
    probe_count = 0
    next_poll = 0
    reloading = exiting = False
    before = after = []
    exit_started = None
    try:
        with logfile.open('wb') as log:
            while time.monotonic() - started < timeout:
                if select.select([master], [], [], 0.05)[0]:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError as exc:
                        if exc.errno != errno.EIO:
                            raise
                        break
                    if not chunk:
                        break
                    output += chunk
                    log.write(chunk)
                    log.flush()
                now = time.monotonic()
                if not command_sent and marker(output, 'CONFIGURED'):
                    os.write(master, b"_dotfiles_benchmark_prompt\n")
                    command_sent = True
                if prompt is None and marker(output, 'PROMPT'):
                    prompt = now - started
                completed_probes = output.count(b'__DOTFILES_PROBED__\r\n')
                if completed_probes > probe_count:
                    probe_count = completed_probes
                    probe_inflight = False
                if marker(output, 'FEATURES_FAILED'):
                    break
                if prompt is not None and features is None and not probe_inflight and now >= next_poll:
                    # One probe in flight; never fill the PTY input while Deno initializes.
                    os.write(master, b"_dotfiles_benchmark_features\n")
                    probe_inflight = True
                    next_poll = now + .2
                if features is None and marker(output, 'FEATURES'):
                    features = now - started
                if features is not None and not reloading and now - started - prompt >= 3:
                    before = server_pids(home)
                    os.write(master, b"_dotfiles_benchmark_reload\n")
                    reloading = True
                if not exiting and marker(output, 'RELOADED'):
                    after = server_pids(home)
                    os.write(master, b"_dotfiles_benchmark_exit\n")
                    exiting = True
                    exit_started = now
                if proc.poll() is not None:
                    break
                if exiting and now - exit_started > 10:
                    break
        if exiting and proc.poll() is None:
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
        graceful = proc.poll() is not None and proc.returncode == 0
        parsed = checks(output)
        leaked = server_pids(home) if graceful else []
        passed = (features is not None and marker(output, 'RELOADED') and graceful
                  and set(parsed) == RELOAD_CHECKS and all(v == 'PASS' for v in parsed.values())
                  and len(before) == 1 and before == after and not leaked)
        return {'prompt_seconds': round(prompt, 3) if prompt is not None else None,
                'features_seconds': round(features, 3) if features is not None else None,
                'reload_checks': parsed, 'server_pids_before_reload': before,
                'server_pids_after_reload': after, 'leaked_server_pids': leaked,
                'graceful_exit': graceful, 'passed': passed}
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
        os.close(master)
        cleanup_plugin_servers(home)


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
    subprocess.run(['/bin/bash', str(ROOT / 'scripts/link.sh')], env=env, check=True,
                   stdout=log, stderr=subprocess.STDOUT)
(home / '.zprofile').write_text('if [[ -x /opt/homebrew/bin/brew ]]; then\n'
                               '  eval "$(/opt/homebrew/bin/brew shellenv)"\n'
                               'elif [[ -x /usr/local/bin/brew ]]; then\n'
                               '  eval "$(/usr/local/bin/brew shellenv)"\nfi\n')
probe_path = shlex.quote(str(ROOT / 'tests/macos/reload-probe.zsh'))
(home / '.zshrc.local').write_text(f'''_dotfiles_benchmark_prompt() {{ print '__DOTFILES_'PROMPT__; }}
_dotfiles_benchmark_features() {{
  if ! zeno-ensure-loaded; then print '__DOTFILES_'FEATURES_FAILED__; return; fi
  if [[ $ZENO_LOADED == 1 && -S $ZENO_SOCK ]] && (( ${{+widgets[history-substring-search-up]}} && ${{+functions[compdef]}} )); then
    print '__DOTFILES_'FEATURES__
  fi
  print '__DOTFILES_'PROBED__
}}
_dotfiles_benchmark_reload() {{ source {probe_path}; print '__DOTFILES_'RELOADED__; }}
_dotfiles_benchmark_exit() {{ unsetopt CHECK_JOBS; builtin exit; }}
print '__DOTFILES_'CONFIGURED__
''')
sessions = []
for index in range(args.warm_runs + 1):
    result = run_shell(env, home, args.timeout, out / f'shell-{index:02d}.log')
    sessions.append(result)
    print(json.dumps({'session': index, **result}), flush=True)
    if not result['passed']:
        break
cold = sessions[0]
warm = sessions[1:]
result = {'passed': len(sessions) == args.warm_runs + 1 and all(s['passed'] for s in sessions),
          'cold_startup_seconds': cold['prompt_seconds'],
          'cold_features_seconds': cold['features_seconds'],
          'sessions': sessions, 'macos_version': platform.mac_ver()[0],
          'architecture': platform.machine(), 'warm_run_count': len(warm),
          'scope': 'isolated HOME; PTY prompt and deferred completion/history/zeno readiness; five reloads per shell; shared host Homebrew'}
if warm and all(s['prompt_seconds'] is not None and s['features_seconds'] is not None for s in warm):
    result.update(warm_median_seconds=round(statistics.median(s['prompt_seconds'] for s in warm), 3),
                  warm_p95_seconds=percentile([s['prompt_seconds'] for s in warm], .95),
                  warm_features_median_seconds=round(statistics.median(s['features_seconds'] for s in warm), 3),
                  warm_features_p95_seconds=percentile([s['features_seconds'] for s in warm], .95))
(out / 'benchmark.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['passed'] else 1)
