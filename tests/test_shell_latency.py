"""Measure shell latency without starting Deno, fzf, or the user's shell config."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ShellLatencyTests(unittest.TestCase):
    def run_zsh(self, code):
        return subprocess.run(['zsh', '-f', '-c', code, 'test',
                               str(ROOT / '.bin/common/latency.zsh')],
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

    def test_invalid_threshold_uses_default(self):
        result = self.run_zsh('source "$1"; DOTFILES_LATENCY_THRESHOLD_MS=oops; '
                              '_dotfiles-record-latency slow 101')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('threshold 100ms', result.stderr)

if __name__ == '__main__':
    unittest.main()
