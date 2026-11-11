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
	@if [ "$$(uname -s)" = Darwin ]; then PYTHON="$(PYTHON)" bash scripts/apps.sh; fi
native-check:
	@if [ "$$(uname -s)" = Darwin ]; then PYTHON="$(PYTHON)" bash scripts/apps.sh --check; fi
test:
	$(PYTHON) -m unittest discover -s tests -v
packages:
	brew bundle --file="$(ROOT)/Brewfile"

.PHONY: system check-system touchid docker check-docker
system:
	bash scripts/macos/defaults.sh
check-system:
	bash scripts/macos/defaults.sh check
touchid:
	bash scripts/macos/sudo-touchid.sh
docker:
	bash scripts/macos/docker.sh
check-docker:
	bash scripts/macos/docker.sh check
