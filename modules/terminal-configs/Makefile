.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON ?= python3
CHEZMOI ?= chezmoi
ROOT := $(CURDIR)
CHEZMOI_ARGS = --source "$(ROOT)" --destination "$(HOME)"
ifneq ($(KEYBOARD_LAYOUT),)
CHEZMOI_ARGS += --override-data '{"keyboardLayout":"$(KEYBOARD_LAYOUT)"}'
endif
.PHONY: help apply check test packages files verify native-apply native-check
help:
	@echo "make apply / check / test / packages"
apply: files
	$(MAKE) native-apply
check: verify
	$(MAKE) native-check
files:
	$(CHEZMOI) $(CHEZMOI_ARGS) apply --error-on-conflict
verify:
	$(CHEZMOI) $(CHEZMOI_ARGS) verify
native-apply:
	@if [ "$$(uname -s)" = Darwin ] && [ -d /Applications/iTerm.app ]; then $(PYTHON) scripts/macos/iterm2.py; fi
native-check:
	@if [ "$$(uname -s)" = Darwin ] && [ -d /Applications/iTerm.app ]; then $(PYTHON) scripts/macos/iterm2.py --check; fi
test:
	$(PYTHON) -m unittest discover -s tests -v
packages:
	brew bundle --file="$(ROOT)/Brewfile"
