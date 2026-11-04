"""Measure shell latency without starting Deno, fzf, or the user's shell config."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ShellLatencyTests(unittest.TestCase):
    def run_zsh(self, code):
        return subprocess.run(['zsh', '-f', '-c', code, 'test',
                               str(ROOT / 'scripts/common/latency.zsh')],
                              capture_output=True, text=True, timeout=5)

    def test_warns_only_at_or_above_threshold(self):
        result = self.run_zsh('source "$1"; DOTFILES_LATENCY_THRESHOLD_MS=100; '
                              '_dotfiles-record-latency fast 99; '
                              '_dotfiles-record-latency slow 100; dotfiles-latency')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('fast:', result.stderr)
        self.assertIn('slow: 100ms', result.stderr)
        self.assertIn('fast', result.stdout)

    def test_wrapper_preserves_failure_and_does_not_run_during_install(self):
        result = self.run_zsh('zeno-init() { print called; return 7; }; source "$1"; '
                              '_dotfiles-measure-zeno-init; _dotfiles-measure-zeno-init; '
                              'print ready; zeno-init; result=$?; '
                              'print result=$result; dotfiles-latency')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('ready\ncalled\nresult=7\n'))
        self.assertEqual(result.stdout.count('called'), 1)
        self.assertIn('zeno-init', result.stdout)

    def test_initialized_calls_do_not_overwrite_first_measurement(self):
        result = self.run_zsh('zeno-init() { ZENO_LOADED=1; }; source "$1"; '
                              '_dotfiles-measure-zeno-init; zeno-init; '
                              'first=$DOTFILES_LATENCY_MS[zeno-init]; zeno-init; '
                              '[[ $first == $DOTFILES_LATENCY_MS[zeno-init] ]]')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shortcut_displays_warning_after_return_even_on_cancel(self):
        result = self.run_zsh('zeno-lazy-widget-dispatch() { '
                              '_dotfiles-record-latency zeno-init 200; '
                              'print -u2 widget-finished; return 130; }; '
                              'source "$1"; WIDGET=zeno-ghq-cd; '
                              '_dotfiles-measure-zeno-shortcuts; '
                              '_dotfiles-measure-zeno-shortcuts; '
                              'zeno-lazy-widget-dispatch; print result=$?')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('result=130', result.stdout)
        self.assertTrue(result.stderr.startswith('widget-finished\n'))
        self.assertIn('zeno-ghq-cd: [latency] zeno-init: 200ms', result.stderr)
        self.assertEqual(result.stderr.count('[latency]'), 1)

    def test_autoload_uses_plugin_root_when_fpath_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            functions = Path(directory) / 'shells/zsh/functions'
            functions.mkdir(parents=True)
            (functions / 'zeno-lazy-widget-dispatch').write_text(
                'function zeno-lazy-widget-dispatch() { print widget-called; return 130; }\n')
            result = self.run_zsh('source "$1"; ZENO_ROOT=' + repr(directory) + '; '
                                  'fpath=(); autoload -Uz zeno-lazy-widget-dispatch; '
                                  '_dotfiles-measure-zeno-shortcuts; '
                                  'zeno-lazy-widget-dispatch; print result=$?')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, 'widget-called\nresult=130\n')
            self.assertEqual(result.stderr, '')

    def test_missing_definition_does_not_replace_original_widget(self):
        result = self.run_zsh('source "$1"; unset ZENO_ROOT; fpath=(); '
                              'autoload -Uz zeno-lazy-widget-dispatch; '
                              '_dotfiles-measure-zeno-shortcuts; '
                              '(( ! $+functions[_dotfiles-original-zeno-dispatch] )); '
                              'print saved=$?')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('saved=0', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_invalid_threshold_uses_default(self):
        result = self.run_zsh('source "$1"; DOTFILES_LATENCY_THRESHOLD_MS=oops; '
                              '_dotfiles-record-latency slow 101')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('threshold 100ms', result.stderr)

if __name__ == '__main__':
    unittest.main()
