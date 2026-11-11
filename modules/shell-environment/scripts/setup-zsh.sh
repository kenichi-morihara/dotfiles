#!/bin/bash

# zshにシェルを変更するスクリプト

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "zshセットアップスクリプト"
echo "=========================================="
echo ""

# zshがインストールされているか確認
if ! command -v zsh &> /dev/null; then
    echo -e "${RED}エラー: zshがインストールされていません${NC}"
    echo ""
    case "$(uname -s)" in
        Darwin)
            echo "macOSの場合、以下のコマンドでインストールできます:"
            echo "  brew install zsh"
            ;;
        Linux)
            echo "Linuxの場合、以下のコマンドでインストールできます:"
            echo "  sudo apt-get install zsh    # Debian/Ubuntu"
            echo "  sudo yum install zsh        # CentOS/RHEL"
            echo "  sudo pacman -S zsh          # Arch Linux"
            ;;
    esac
    exit 1
fi

# zshのパスを取得
ZSH_PATH=$(which zsh)
echo -e "${GREEN}✓ zshが見つかりました: ${ZSH_PATH}${NC}"

# 現在のシェルを確認
CURRENT_SHELL=$(echo $SHELL)
echo "現在のシェル: ${CURRENT_SHELL}"

# 既にzshがデフォルトシェルの場合
if [ "$CURRENT_SHELL" = "$ZSH_PATH" ]; then
    echo -e "${GREEN}既にzshがデフォルトシェルに設定されています${NC}"
    exit 0
fi

# /etc/shellsにzshが登録されているか確認
if ! grep -q "^${ZSH_PATH}$" /etc/shells 2>/dev/null; then
    echo ""
    echo -e "${YELLOW}警告: /etc/shellsにzshが登録されていません${NC}"
    echo "管理者権限で追加する必要があります。"
    echo ""
    read -p "sudoで/etc/shellsに追加しますか？ (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$ZSH_PATH" | sudo tee -a /etc/shells
        echo -e "${GREEN}✓ /etc/shellsに追加しました${NC}"
    else
        echo -e "${YELLOW}スキップしました。手動で追加してください:${NC}"
        echo "  echo '$ZSH_PATH' | sudo tee -a /etc/shells"
        exit 1
    fi
fi

# 確認プロンプト
echo ""
echo -e "${YELLOW}デフォルトシェルをzshに変更しますか？${NC}"
echo "  現在: ${CURRENT_SHELL}"
echo "  変更後: ${ZSH_PATH}"
echo ""
read -p "続行しますか？ (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "キャンセルしました"
    exit 0
fi

# chshを実行
echo ""
echo "シェルを変更しています..."
if chsh -s "$ZSH_PATH"; then
    echo -e "${GREEN}✓ シェルをzshに変更しました${NC}"
    echo ""
    echo "変更を反映するには、以下のいずれかを実行してください:"
    echo "  1. 新しいターミナルを開く"
    echo "  2. 現在のシェルで 'exec zsh' を実行"
    echo ""
else
    echo -e "${RED}エラー: シェルの変更に失敗しました${NC}"
    exit 1
fi
