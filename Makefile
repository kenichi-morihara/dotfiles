.DEFAULT_GOAL := help

SHELL := /bin/bash
ROOT := $(shell pwd)
CHEZMOI ?= chezmoi
PYTHON ?= python3
PROFILE ?= core

.PHONY: help init diff dry-run apply apply-files status verify rectangle macos-init packages packages-check runtimes shell-setup test

help: ## 操作一覧を表示（既定）
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' Makefile

init: ## 初回移行・設定配布・chezmoi登録（既存設定を退避）
	CHEZMOI_BIN="$$(command -v "$(CHEZMOI)")" bash .bin/link.sh

diff: ## 配布するファイルの差分を表示
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" diff

dry-run: ## ファイル配布をプレビュー（Rectangleは実行しない）
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" apply --dry-run --verbose --error-on-conflict

apply: ## ファイル配布とmacOSのRectangle設定を順に適用
	$(MAKE) apply-files
	@if [ "$$(uname -s)" = Darwin ]; then $(MAKE) rectangle; fi

apply-files: ## chezmoiの管理ファイルだけを適用（競合時は停止）
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" apply --error-on-conflict

status: ## 配布先ファイルの変更状況を表示
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" status

verify: ## 配布先ファイルが宣言と一致するか検証
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" verify

rectangle: ## Rectangleの6ショートカットを適用（macOS）
	bash .bin/macos/rectangle.sh

macos-init: ## Command Line Tools・Homebrewを準備（macOS）
	bash .bin/macos/init.sh

packages: ## Homebrewパッケージを導入（PROFILE=core/full、既定core）
	bash .bin/macos/brew.sh --profile "$(PROFILE)"

packages-check: ## Homebrewパッケージの不足を確認
	bash .bin/macos/brew.sh --profile "$(PROFILE)" check

runtimes: ## mise管理の言語ランタイムを導入（設定配布後）
	mise install

shell-setup: ## zshをログインシェルに設定
	bash setup-zsh.sh

test: ## 一時HOMEなどを使った既存テストを実行
	$(PYTHON) -m unittest discover -s tests -v
