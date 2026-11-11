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
	STANDALONE=1 $(PYTHON) scripts/install.py --default
native-check:
	$(PYTHON) scripts/check.py
test:
	$(PYTHON) -m unittest discover -s tests -v
packages:
	brew bundle --file="$(ROOT)/Brewfile"
