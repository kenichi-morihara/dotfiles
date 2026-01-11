from ranger.api.commands import Command
import subprocess
import shlex
import os

class openwithfzf(Command):
    """:openwithfzf

    Select macOS application via fzf and open file with it
    """

    def execute(self):
        file = self.fm.thisfile.path

        # /Applications と ~/Applications を対象にする
        cmd = r'''
        find /Applications ~/Applications -maxdepth 1 -name "*.app" -type d 2>/dev/null \
        | sed 's#.*/##' \
        | sort \
        | fzf --prompt="Open with > "
        '''

        try:
            p = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            )
            app = p.stdout.read().strip()
        except Exception:
            # fzf終了後に画面をリレンダリング
            self.fm.ui.need_redraw = True
            return

        if not app:
            # fzfをキャンセルした場合も画面をリレンダリング
            self.fm.ui.need_redraw = True
            return

        subprocess.Popen([
            "open",
            "-a",
            app,
            file
        ])
        
        # コマンド終了後に画面をリレンダリング
        self.fm.ui.need_redraw = True
