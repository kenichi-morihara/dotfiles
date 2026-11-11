source "${${(%):-%x}:A:h}/../../modules/shell-environment/scripts/common/.zshrc"
case "$(uname -s)" in
  Darwin) source "${${(%):-%x}:A:h}/../macos/brew.zsh" ;;
  Linux) source "${${(%):-%x}:A:h}/../linux/yay.zsh" ;;
esac
