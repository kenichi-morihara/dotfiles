import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]


sys.path.insert(0, str(ROOT / 'tests/macos'))
from probe_results import checks, marker


class ProbeTests(unittest.TestCase):
    def test_ignores_echoed_commands_and_accepts_only_output(self):
        output = (b'prompt> print "__CHECK_${tool}=FAIL"\r\n'
                  b'__CHECK_brew=PASS\r\n__CHECK_mise=FAIL\r\n'
                  b"prompt> print '__DOTFILES_'DONE__\r\n")
        self.assertEqual(checks(output), {'brew': 'PASS', 'mise': 'FAIL'})
        self.assertFalse(marker(output, 'DONE'))
        self.assertTrue(marker(output + b'__DOTFILES_DONE__\r\n', 'DONE'))


class SetupTests(unittest.TestCase):
    def test_brewfile_does_not_install_unavailable_fig(self):
        brewfile = (ROOT / '.bin/macos/.Brewfile').read_text()
        self.assertNotIn('cask "fig"', brewfile)

    def test_brewfile_does_not_tap_retired_builtin_bundle(self):
        brewfile = (ROOT / '.bin/macos/.Brewfile').read_text()
        self.assertNotIn('tap "homebrew/bundle"', brewfile)

    def test_brewfile_uses_corepack_without_competing_yarn_binaries(self):
        brewfile = (ROOT / '.bin/macos/.Brewfile').read_text()
        self.assertIn('brew "corepack"', brewfile)
        self.assertNotIn('brew "yarn"', brewfile)
        self.assertNotIn('npm "corepack"', brewfile)

    def test_core_profile_contains_interactive_shell_dependencies(self):
        brewfile = (ROOT / '.bin/macos/.Brewfile.core').read_text()
        full = (ROOT / '.bin/macos/.Brewfile').read_text()
        for package in ('deno', 'fzf', 'ghq', 'corepack', 'lua', 'mise', 'ranger', 'starship', 'zinit'):
            with self.subTest(package=package):
                self.assertIn(f'brew "{package}"', brewfile)
                self.assertIn(f'brew "{package}"', full)

    def test_mise_config_is_the_only_global_runtime_declaration(self):
        self.assertFalse((ROOT / '.tool-versions').exists())
        config = (ROOT / '.config/mise/config.toml').read_text()
        self.assertIn('node = "25.2.1"', config)
        self.assertIn('python = "3.14"', config)
        self.assertIn('deno = "2.6.5"', config)

    def test_zeno_bindings_work_before_lazy_initialization(self):
        result = subprocess.run(['zsh', '-f', '-c',
                                 'unset ZENO_LOADED; ZENO_BOOTSTRAPPED=1; source "$1"; bindkey "^g"; bindkey "^i"',
                                 'test', str(ROOT / '.bin/common/zeno.zsh')],
                                text=True, capture_output=True, check=True)
        self.assertIn('zeno-ghq-cd', result.stdout)
        self.assertIn('zeno-completion', result.stdout)

    def test_shell_syntax(self):
        scripts = [("bash", ROOT / "setup-zsh.sh")]
        scripts += [("bash", p) for p in (ROOT / ".bin").rglob("*.sh")]
        scripts += [("zsh", p) for p in (ROOT / ".bin").rglob("*.zsh")]
        scripts.append(("zsh", ROOT / ".bin/common/.zshrc"))
        scripts += [("bash", p) for p in (ROOT / "tests/macos").glob("*.sh")]
        for shell, path in scripts:
            with self.subTest(path=str(path.relative_to(ROOT))):
                subprocess.run([shell, '-n', str(path)], check=True, capture_output=True)

    def test_links_are_repeatable_and_preserve_existing_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.zshrc').write_text('original shell')
            config = home / '.config/zeno'
            config.mkdir(parents=True)
            (config / 'local.yml').write_text('local settings')
            (config / 'config.yml').write_text('original config')
            env = dict(os.environ, HOME=tmp)
            for _ in range(2):
                subprocess.run(['bash', str(ROOT / '.bin/link.sh')], env=env,
                               check=True, capture_output=True)
            self.assertEqual((home / '.zshrc.backup').read_text(), 'original shell')
            self.assertEqual((config / 'config.yml.backup').read_text(), 'original config')
            self.assertEqual((config / 'local.yml').read_text(), 'local settings')
            self.assertEqual((config / 'config.yml').resolve(), ROOT / '.config/zeno/config.yml')
            self.assertFalse((config / 'zeno').exists())
            self.assertFalse((home / '.config/windows').exists())

    def test_linker_removes_only_legacy_tool_versions_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'home'
            home.mkdir()
            legacy = home / '.tool-versions'
            legacy.symlink_to(ROOT / '.tool-versions')
            subprocess.run(['bash', str(ROOT / '.bin/link.sh')],
                           env=dict(os.environ, HOME=str(home)), check=True, capture_output=True)
            self.assertFalse(legacy.exists())
            self.assertFalse(legacy.is_symlink())

            local = home / '.tool-versions'
            local.write_text('node 20.0.0\n')
            subprocess.run(['bash', str(ROOT / '.bin/link.sh')],
                           env=dict(os.environ, HOME=str(home)), check=True, capture_output=True)
            self.assertEqual(local.read_text(), 'node 20.0.0\n')

    def test_directory_symlink_does_not_modify_original_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'home'
            original = Path(tmp) / 'original'
            home.mkdir()
            original.mkdir()
            (original / 'config.yml').write_text('keep')
            (home / '.config').mkdir()
            (home / '.config/zeno').symlink_to(original)
            subprocess.run(['bash', str(ROOT / '.bin/link.sh')],
                           env=dict(os.environ, HOME=str(home)), check=True, capture_output=True)
            self.assertEqual((original / 'config.yml').read_text(), 'keep')
            self.assertTrue((home / '.config/zeno.backup').is_symlink())

    def test_init_skips_installed_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, body in [('uname', 'echo Darwin'), ('xcode-select', 'exit 0'),
                               ('brew', 'exit 0'), ('curl', 'echo unexpected-download >&2; exit 99')]:
                path = Path(tmp) / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            result = subprocess.run(['bash', str(ROOT / '.bin/macos/init.sh')],
                                    env=dict(os.environ, PATH=tmp + ':/usr/bin:/bin'),
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('unexpected-download', result.stderr)

    def test_brew_wrapper_commits_only_brewfile_and_pushes_to_local_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / 'repo'
            remote = base / 'remote.git'
            bindir = base / 'bin'
            bindir.mkdir()
            brew = bindir / 'brew'
            brew.write_text('#!/bin/sh\nif [ "$1" = bundle ]; then\n'
                            '  for arg in "$@"; do\n'
                            '    case "$arg" in --file=*) echo new > "${arg#--file=}";; esac\n'
                            '  done\nfi\n')
            brew.chmod(0o755)
            env = dict(os.environ, HOME=tmp, GIT_CONFIG_NOSYSTEM='1',
                       GIT_CONFIG_GLOBAL=os.devnull, PATH=str(bindir) + ':/usr/bin:/bin')

            def git(*args):
                return subprocess.run(['git', *args], env=env, check=True,
                                      text=True, capture_output=True).stdout.strip()

            git('init', '--bare', str(remote))
            git('init', '-b', 'main', str(repo))
            git('-C', str(repo), 'config', 'user.name', 'Test')
            git('-C', str(repo), 'config', 'user.email', 'test@example.invalid')
            brewfile = repo / '.bin/macos/.Brewfile'
            brewfile.parent.mkdir(parents=True)
            brewfile.write_text('old\n')
            (repo / 'unrelated').write_text('original')
            git('-C', str(repo), 'add', '.')
            git('-C', str(repo), 'commit', '-m', 'initial')
            git('-C', str(repo), 'remote', 'add', 'origin', str(remote))
            git('-C', str(repo), 'push', '-u', 'origin', 'main')
            (repo / 'unrelated').write_text('work in progress')
            git('-C', str(repo), 'add', 'unrelated')
            script = ('source "$1"; _DOTFILES_DIR="$2"; '
                      'BREWFILE_PATH="$2/.bin/macos/.Brewfile"; brew install example')
            result = subprocess.run(['zsh', '-f', '-c', script, 'test',
                                     str(ROOT / '.bin/macos/brew.zsh'), str(repo)],
                                    env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(git('-C', str(repo), 'diff', '--cached', '--name-only'), 'unrelated')
            self.assertEqual(git('-C', str(repo), 'show', '--pretty=', '--name-only', 'HEAD'),
                             '.bin/macos/.Brewfile')
            self.assertEqual(git('-C', str(repo), 'rev-parse', 'HEAD'),
                             git('--git-dir=' + str(remote), 'rev-parse', 'refs/heads/main'))

    def test_brew_bundle_uses_repository_brewfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp)
            for name, body in [('uname', 'echo Darwin'), ('brew', 'printf "%s\\n" "$@"')]:
                path = bin_dir / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            env = dict(os.environ, HOME=tmp, PATH=tmp + ':' + os.environ['PATH'])
            result = subprocess.run(['bash', str(ROOT / '.bin/macos/brew.sh')],
                                    env=env, text=True, capture_output=True, check=True)
            self.assertIn('--file=' + str(ROOT / '.bin/macos/.Brewfile'), result.stdout)

    def test_brew_bundle_accepts_core_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            bindir = Path(tmp)
            for name, body in [('uname', 'echo Darwin'), ('brew', 'printf "%s\\n" "$@"')]:
                path = bindir / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            env = dict(os.environ, HOME=tmp, PATH=tmp + ':' + os.environ['PATH'])
            result = subprocess.run(['bash', str(ROOT / '.bin/macos/brew.sh'),
                                     '--profile', 'core', 'check'], env=env,
                                    text=True, capture_output=True, check=True)
            self.assertIn('--file=' + str(ROOT / '.bin/macos/.Brewfile.core'), result.stdout)
            self.assertIn('check', result.stdout)


if __name__ == '__main__':
    unittest.main()
