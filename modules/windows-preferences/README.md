# Windows のオーバーレイ・常駐設定

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は windows です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## Windows での利用
PowerShell から scripts/windows/configure.ps1 を実行して適用し、-Check を付けて読み取り確認します。
make apply / check は Git Bash と Make がある Windows 環境で利用できます。
Game DVR と NVIDIA Overlay、Armoury Crate の機種固有設定を含みます。宣言は home/dot_config/windows にあります。必要な項目を選んでから適用してください。
tests/read-only.ps1 はリソース取得を模擬し、書き込みコマンドが呼ばれないことを検証します。
