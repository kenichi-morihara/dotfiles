"""Distrusted CA roots: bundle editing, shell environment, and make doctor.

All tests use a fixture bundle via CA_BUNDLE; /etc/ssl/cert.pem is never touched.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CA_SH = ROOT / 'scripts/macos/ca-certs.sh'
CA_ZSH = ROOT / 'scripts/macos/ca-certs.zsh'
DOCTOR = ROOT / 'scripts/macos/doctor.sh'

TARGETS = ('AAA Certificate Services', 'emSign ECC Root CA - G3')
KEEP = ('Keep One', 'Keep Two')


def block(name):
    return (f'### /C=XX/CN={name}\n\n=== /C=XX/CN={name}\nCertificate:\n'
            f'    Data:\n        Subject: C=XX, CN={name}\n'
            f'-----BEGIN CERTIFICATE-----\n{name.replace(" ", "")}\n-----END CERTIFICATE-----\n\n')


def bundle_text(*names):
    return '# fixture bundle\n' + ''.join(block(n) for n in names)


class Fixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.bundle = self.dir / 'cert.pem'

    def write_bundle(self, *names):
        self.bundle.write_text(bundle_text(*names))

    def env(self, **extra):
        env = dict(os.environ, CA_BUNDLE=str(self.bundle))
        for key in ('SSL_CERT_FILE', 'PIP_CERT', 'NODE_OPTIONS', 'NODE_EXTRA_CA_CERTS'):
            env.pop(key, None)
        env.update(extra)
        return env

    def run_script(self, *cmd, **extra_env):
        return subprocess.run(list(cmd), env=self.env(**extra_env),
                              capture_output=True, text=True, timeout=20)


class CaCertsScriptTests(Fixture):
    def test_check_fails_while_a_target_root_is_present(self):
        self.write_bundle(KEEP[0], TARGETS[0])
        self.assertEqual(self.run_script('bash', str(CA_SH), 'check').returncode, 1)

    def test_check_passes_when_no_target_root_is_present(self):
        self.write_bundle(*KEEP)
        self.assertEqual(self.run_script('bash', str(CA_SH), 'check').returncode, 0)

    def test_apply_removes_only_target_roots(self):
        self.write_bundle(KEEP[0], TARGETS[0], KEEP[1], TARGETS[1])
        result = self.run_script('bash', str(CA_SH), 'apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        text = self.bundle.read_text()
        for name in TARGETS:
            self.assertNotIn(name, text)
        for name in KEEP:
            self.assertIn(block(name), text)
        self.assertEqual(text.count('BEGIN CERTIFICATE'), 2)

    def test_apply_is_idempotent(self):
        self.write_bundle(KEEP[0], TARGETS[0])
        self.run_script('bash', str(CA_SH), 'apply')
        first = self.bundle.read_text()
        result = self.run_script('bash', str(CA_SH), 'apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.bundle.read_text(), first)

    def test_backup_keeps_the_first_pristine_copy(self):
        self.write_bundle(KEEP[0], TARGETS[0])
        pristine = self.bundle.read_text()
        self.run_script('bash', str(CA_SH), 'apply')
        # An OS update restores the roots; the old backup must not be overwritten.
        self.write_bundle(KEEP[0], KEEP[1], TARGETS[1])
        self.run_script('bash', str(CA_SH), 'apply')
        self.assertEqual(Path(str(self.bundle) + '.bak').read_text(), pristine)

    def test_unknown_mode_is_rejected(self):
        self.write_bundle(*KEEP)
        self.assertEqual(self.run_script('bash', str(CA_SH), 'bogus').returncode, 2)


class CaCertsShellEnvTests(Fixture):
    def source(self, preset=''):
        script = f'{preset}\nsource "{CA_ZSH}"\nprint -r -- "SSL=$SSL_CERT_FILE|PIP=$PIP_CERT|EXTRA=$NODE_EXTRA_CA_CERTS|NODE=$NODE_OPTIONS"'
        return self.run_script('zsh', '-c', script).stdout.strip()

    def test_exports_bundle_for_openssl_pip_and_node(self):
        self.write_bundle(*KEEP)
        self.assertEqual(self.source(), f'SSL={self.bundle}|PIP={self.bundle}|EXTRA={self.bundle}|NODE=--use-openssl-ca')

    def test_does_nothing_when_the_bundle_is_missing(self):
        self.assertEqual(self.source(), 'SSL=|PIP=|EXTRA=|NODE=')

    def test_node_options_are_preserved_and_not_duplicated(self):
        self.write_bundle(*KEEP)
        out = self.source('export NODE_OPTIONS="--max-old-space-size=4096"\nsource "' + str(CA_ZSH) + '"')
        self.assertTrue(out.endswith('NODE=--max-old-space-size=4096 --use-openssl-ca'), out)


class DoctorTests(Fixture):
    def doctor(self):
        return self.run_script('bash', str(DOCTOR))

    def test_passes_when_bundle_is_clean_and_env_is_configured(self):
        self.write_bundle(*KEEP)
        result = self.doctor()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fails_and_points_to_the_fix_when_a_root_remains(self):
        self.write_bundle(KEEP[0], TARGETS[1])
        result = self.doctor()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('make ca-certs', result.stdout + result.stderr)

    def test_fails_when_the_bundle_is_missing(self):
        self.assertNotEqual(self.doctor().returncode, 0)


if __name__ == '__main__':
    unittest.main()
