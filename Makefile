.DEFAULT_GOAL := help

SHELL := /bin/bash
ROOT := $(CURDIR)
CHEZMOI ?= chezmoi
PYTHON ?= python3
export DOTFILES_PROFILE_PYTHON := $(PYTHON)
PROFILE ?=
PROFILE_TOOL = $(PYTHON) scripts/common/profiles.py
PROFILE_STATE = $(if $(XDG_CONFIG_HOME),$(XDG_CONFIG_HOME),$(HOME)/.config)/dotfiles/profile

.PHONY: help help-all

help: ## 普段使う操作（既定）
	@awk 'BEGIN {FS = ":.*## "; print "普段使う操作"} /^(setup|apply|check|diff|profile-select|setup-plan|test):.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf '\n全操作は make help-all で確認できます。\n'

help-all: ## 全操作を用途別に表示
	@awk 'BEGIN {FS = ":.*## "} /^##@ / {printf "\n%s\n", substr($$0, 5)} /^[a-zA-Z_-]+:.*## / {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

include make/core.mk
include make/maintenance.mk
