"""Check privilege handling and failure ordering without installing packages."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MacOSSetupTests(unittest.TestCase):
    def run_setup(self, fail=''):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            log = directory / 'calls'
            scripts = {
                'uname': 'echo Darwin',
                'id': 'echo 501',
                'brew': 'exit 0',
                'sudo': 'echo "sudo $*" >> "$CALL_LOG"; '
                        '[ "$FAIL_STEP" != auth ] || exit 1; '
                        'if [ "$*" = "-n -v" ] && [ -f "$AUTH_REVOKED" ]; then '
                        'echo "sudo: a password is required" >&2; exit 1; fi',
                'make': 'echo "make $*" >> "$CALL_LOG"; '
                        'if [ "$1" = packages ]; then '
                        'case "$FAIL_STEP" in '
                        'packages) exit 7 ;; '
                        'homebrew-probe) '
                        '# Model Homebrew utils/sudo.sh invalidating the cached credential.\n'
                        'if [ "${HOMEBREW_SUDO_CHECKED:-}" != 1 ]; then touch "$AUTH_REVOKED"; fi; '
                        'sudo -n -v || exit 7 ;; '
                        'expired) touch "$AUTH_REVOKED" ;; '
                        'esac; fi',
            }
            for name, body in scripts.items():
                path = directory / name
                path.write_text('#!/bin/bash\n' + body + '\n')
                path.chmod(0o755)
            env = dict(os.environ, PATH=str(directory) + ':' + os.environ['PATH'],
                       CALL_LOG=str(log), FAIL_STEP=fail, AUTH_REVOKED=str(directory / "revoked"))
            env.pop("HOMEBREW_SUDO_CHECKED", None)
            result = subprocess.run(['bash', str(ROOT / 'scripts/macos/setup.sh')],
                                    env=env, capture_output=True, text=True, timeout=10)
            # Touch ID setup is idempotent: an already-enabled host skips its sudo call.
            calls = [line for line in log.read_text().splitlines()
                     if not line.startswith('sudo /bin/bash ')]
            return result, calls

    def test_homebrew_privilege_probe_does_not_revoke_setup_authentication(self):
        result, calls = self.run_setup('homebrew-probe')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('make apply', calls)

    def test_expired_authentication_stops_before_settings_with_actionable_error(self):
        result, calls = self.run_setup('expired')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('make apply', calls)
        self.assertIn('sudo -v', result.stderr)
        self.assertNotIn('Setup complete', result.stdout)

    def test_authenticate_then_packages_then_apply(self):
        result, calls = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['sudo -v', 'make packages PROFILE=full', 'sudo -n -v', 'make apply'])

    def test_package_failure_stops_before_apply(self):
        result, calls = self.run_setup('packages')
        self.assertEqual(result.returncode, 7)
        self.assertEqual(calls, ['sudo -v', 'make packages PROFILE=full'])

    def test_auth_failure_runs_no_make_commands(self):
        result, calls = self.run_setup('auth')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, ['sudo -v'])

if __name__ == '__main__':
    unittest.main()
