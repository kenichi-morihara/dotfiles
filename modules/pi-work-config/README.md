# Pi と Claude CLI の接続

このディレクトリをコピーし、その中から利用できます。

```sh
make packages  # Homebrew を利用する場合
make apply
make check
make test
```

設定本体は home/、処理は scripts/、検証は tests/ にあります。chezmoi と Python 3 を使います。対応 OS は darwin, linux です。

別リポジトリにする場合は、このディレクトリの内容を新しいリポジトリのルートへコピーします。親の dotfiles を参照するコードは必要ありません。アプリ本体の導入・認証と OS の初回権限は各ツールの手順に従います。

## 単体導入と互換性
単体の make apply は STANDALONE=1 を使い、親 dotfiles の profile を要求せず明示的に有効化します。
Node.js 22.19 以上と mise、公式 Claude CLI の Team ログインが必要です。導入スクリプト内の Node 実行は mise exec を使用します。
dotfiles からの make pi-setup は従来の仕事用 profile 判定を使います。
~/.config/dotfiles/pi のランタイム・設定・セッション、既存の ~/.pi/agent、過去の pi-retired バックアップを保持します。旧 lead 構成の引継ぎ処理も残しています。
通常の pi ランチャーを利用し、make check はインストール済みランタイムのバージョンを確認します。
