"""Check privilege handling and failure ordering without installing packages."""
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MacOSSetupTests(unittest.TestCase):
    def run_setup(self, fail=''):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            log = directory / 'calls'
            # Keep the real setup orchestration, but never inspect or change the
            # host's PAM configuration (including when CI runs on Linux).
            fixture_scripts = directory / 'repo/scripts/macos'
            fixture_scripts.mkdir(parents=True)
            setup = fixture_scripts / 'setup.sh'
            shutil.copyfile(ROOT / 'scripts/macos/setup.sh', setup)
            (fixture_scripts / 'sudo-touchid.sh').write_text(
                '#!/bin/bash\necho touchid >> "$CALL_LOG"\n'
                '[ "$FAIL_STEP" != touchid ] || exit 9\n')
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
            result = subprocess.run(['bash', str(setup)],
                                    env=env, capture_output=True, text=True, timeout=10)
            calls = log.read_text().splitlines()
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
        self.assertEqual(calls, ['sudo -v', 'touchid', 'make packages PROFILE=full', 'sudo -n -v', 'make apply'])

    def test_package_failure_stops_before_apply(self):
        result, calls = self.run_setup('packages')
        self.assertEqual(result.returncode, 7)
        self.assertEqual(calls, ['sudo -v', 'touchid', 'make packages PROFILE=full'])

    def test_touchid_failure_stops_before_packages(self):
        result, calls = self.run_setup('touchid')
        self.assertEqual(result.returncode, 9)
        self.assertEqual(calls, ['sudo -v', 'touchid'])
        self.assertNotIn('Setup complete', result.stdout)

    def test_auth_failure_runs_no_make_commands(self):
        result, calls = self.run_setup('auth')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, ['sudo -v'])

if __name__ == '__main__':
    unittest.main()
