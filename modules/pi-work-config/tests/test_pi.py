"""Exercise company Pi setup and launchers with a disposable home and stub CLIs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PI = ROOT / 'scripts'


class PiSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.bin_dir = self.home / 'bin'
        self.bin_dir.mkdir()
        self.state = self.home / '.config/dotfiles'
        self.root = self.state / 'pi'
        self.launchers = self.home / '.local/bin'
        self.stub('mise', '''printf '%s\n' "$*" >> "$HOME/calls"
if [ "$3" = node ]; then exit 0; fi
prefix="$6"
mkdir -p "$prefix/node_modules/.bin" "$prefix/node_modules/claude-code-pi/src"
cp "$HOME/bin/pi-stub" "$prefix/node_modules/.bin/pi"
touch "$prefix/node_modules/claude-code-pi/src/index.ts"
''')
        self.stub('pi-stub', '''printf '%s\n' "$PI_CODING_AGENT_DIR" "${PI_CODING_AGENT_SESSION_DIR:-}" "$@" > "$HOME/pi-call"
exec "$CLAUDE_CODE_PI_BIN" -p
''')
        self.stub('claude', '''printf '%s\n' "$PWD" "${ANTHROPIC_API_KEY:-}" "${CLAUDE_CODE_OAUTH_TOKEN:-}" "$@" >> "$HOME/claude-calls"
if [ "$1" = auth ]; then
    printf '{"loggedIn":%s,"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":"team"}\n' "${STUB_LOGGED_IN:-true}"
else
    exit "${STUB_CLAUDE_EXIT:-0}"
fi
''')
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / '.config'),
                        PATH=f'{self.launchers}:{self.bin_dir}:{os.environ["PATH"]}')

    def stub(self, name, body):
        path = self.bin_dir / name
        path.write_text('#!/bin/sh\nset -eu\n' + body)
        path.chmod(0o755)

    def select(self, profile):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / 'profile').write_text(profile + '\n')

    def install(self, profile=None):
        if profile:
            self.select(profile)
        return subprocess.run(['bash', str(PI / 'install.sh')], env=self.env,
                              capture_output=True, text=True)

    def launch(self, *args, **env):
        if not shutil.which('node'):
            self.skipTest('node not installed')
        return subprocess.run([str(self.launchers / 'pi'), *args], env=dict(self.env, **env),
                              capture_output=True, text=True)

    def assert_nothing_installed(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / 'calls').exists())
        self.assertFalse((self.home / '.pi').exists())
        self.assertFalse(self.root.exists())

    def test_settings_are_valid_json(self):
        settings = json.loads((PI / 'agent/settings.json').read_text())
        self.assertEqual(settings['defaultProjectTrust'], 'never')
        self.assertEqual((settings['defaultProvider'], settings['defaultModel']),
                         ('claude-code-cli', 'sonnet'))

    def test_stops_without_work_profile(self):
        self.assert_nothing_installed(self.install())
        self.assert_nothing_installed(self.install('personal'))

    def test_explicit_standalone_install_needs_no_parent_profile(self):
        self.env["STANDALONE"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / ".standalone").is_file())

    def test_install_isolated(self):
        agent = self.home / '.pi/agent'
        agent.mkdir(parents=True)
        (agent / 'settings.json').write_text('{"old": true}\n')
        (agent / 'auth.json').write_text('{"token": "keep"}\n')
        result = self.install('work/laptop')
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.home / 'calls').read_text()
        self.assertIn('npm install --prefix', calls)
        self.assertIn('--ignore-scripts --no-save --no-package-lock '
                      '@earendil-works/pi-coding-agent@1.5.1 claude-code-pi@1.2.1', calls)
        company_agent = self.root / 'agent'
        self.assertEqual((company_agent / 'settings.json').read_text(), (PI / 'agent/settings.json').read_text())
        self.assertEqual((agent / 'settings.json').read_text(), '{"old": true}\n')
        self.assertEqual((agent / 'auth.json').read_text(), '{"token": "keep"}\n')
        self.assertEqual([path.name for path in self.launchers.iterdir()], ['pi'])
        self.assertFalse((company_agent / 'extensions').exists())
        session = company_agent / 'sessions/example.jsonl'
        session.parent.mkdir()
        session.write_text('keep')
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(session.read_text(), 'keep')
        self.assertEqual((self.home / 'calls').read_text().count('npm install'), 1)

    def test_migration_keeps_lead_sessions_and_archives_old_entries(self):
        for role in ('member', 'lead'):
            sessions = self.root / role / 'sessions'
            sessions.mkdir(parents=True)
            (sessions / 'example.jsonl').write_text(role)
        self.launchers.mkdir(parents=True)
        for name in ('pi-work', 'pi-work-lead'):
            (self.launchers / name).touch()
        result = self.install('work')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / 'agent/sessions/example.jsonl').read_text(), 'lead')
        self.assertFalse((self.root / 'member').exists())
        self.assertFalse((self.root / 'lead').exists())
        self.assertEqual([path.name for path in self.launchers.iterdir()], ['pi'])
        archive, = self.state.glob('pi-retired.*')
        self.assertEqual((archive / 'member/sessions/example.jsonl').read_text(), 'member')
        self.assertTrue((archive / 'pi-work-lead').exists())

    def test_existing_unrelated_local_pi_is_preserved(self):
        self.launchers.mkdir(parents=True)
        existing = self.launchers / 'pi'
        existing.write_text('local pi')
        self.assert_nothing_installed(self.install('work'))
        self.assertEqual(existing.read_text(), 'local pi')

    def test_work_launch_loads_only_the_provider(self):
        self.assertEqual(self.install('work').returncode, 0)
        result = self.launch('-p', 'OK', PI_CODING_AGENT_DIR='wrong',
                             PI_CODING_AGENT_SESSION_DIR='wrong',
                             ANTHROPIC_API_KEY='fake', CLAUDE_CODE_OAUTH_TOKEN='fake')
        self.assertEqual(result.returncode, 0, result.stderr)
        call = (self.home / 'pi-call').read_text().splitlines()
        self.assertEqual(call[:2], [str(self.root / 'agent'), ''])
        self.assertIn('確認なし', result.stderr)
        self.assertEqual(call.count('-e'), 1)
        self.assertTrue(call[call.index('-e') + 1].endswith('claude-code-pi/src/index.ts'))
        self.assertIn('claude-code-cli/sonnet', call)
        self.assertIn('--no-approve', call)
        calls = (self.home / 'claude-calls').read_text()
        self.assertIn(f'{self.root}\n\n\nauth\nstatus\n--json\n', calls)
        self.assertIn(f'{self.root}\n\n\n-p\n--setting-sources\n\n', calls)
        self.assertNotIn('fake', calls)

    def test_personal_profile_uses_existing_pi(self):
        self.assertEqual(self.install('work').returncode, 0)
        self.select('personal')
        self.stub('pi', 'printf "%s\\n" "$@"\n')
        result = self.launch('--original-option')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '--original-option\n')
        self.assertFalse((self.home / 'claude-calls').exists())

    def test_launch_stops_on_missing_login(self):
        self.assertEqual(self.install('work').returncode, 0)
        self.assertNotEqual(self.launch(STUB_LOGGED_IN='false').returncode, 0)
        self.assertFalse((self.home / 'pi-call').exists())

    def test_launch_rejects_model_override_and_propagates_cli_error(self):
        self.assertEqual(self.install('work').returncode, 0)
        self.assertEqual(self.launch('--model', 'anthropic/sonnet').returncode, 2)
        self.assertFalse((self.home / 'claude-calls').exists())
        self.assertEqual(self.launch(STUB_CLAUDE_EXIT='17').returncode, 17)

    def test_not_distributed_by_chezmoi(self):
        self.assertEqual((ROOT / '.chezmoiroot').read_text().strip(), 'home')

if __name__ == '__main__':
    unittest.main()
