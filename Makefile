.DEFAULT_GOAL := help

SHELL := /bin/bash
ROOT := $(shell pwd)
CHEZMOI ?= chezmoi
PYTHON ?= python3
PROFILE ?= core

.PHONY: help setup init apply check diff dry-run status \
	apply-files apply-apps apply-system verify check-apps \
	macos-init sudo-touchid ca-certs doctor doctor-online packages packages-check runtimes shell-setup test

help: ## 操作一覧（既定）
	@awk 'BEGIN {FS = ":.*## "} /^##@ / {printf "\n%s\n", substr($$0, 5)} /^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' Makefile

##@ 普段使う操作
setup: PROFILE = full
setup: ## sudo認証→パッケージ導入→設定適用（macOS、既定full）
	bash scripts/macos/setup.sh "$(PROFILE)"

apply: ## ファイル→アプリ設定を適用（パッケージ導入なし）
	$(MAKE) apply-files
	$(MAKE) apply-apps

check: ## ファイルとアプリ設定の一致を確認（変更なし）
	$(MAKE) verify
	$(MAKE) check-apps

diff: ## 配布するファイルの差分
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" diff

##@ 初回準備（macOS）
macos-init: ## Command Line Tools・Homebrewを準備
	bash scripts/macos/init.sh

init: ## 初回移行・ファイル配布・chezmoi登録（既存設定を退避）
	CHEZMOI_BIN="$$(command -v "$(CHEZMOI)")" bash scripts/link.sh

sudo-touchid: ## sudoのTouch IDを有効化（初回は管理者認証）
	bash scripts/macos/sudo-touchid.sh

ca-certs: ## /etc/ssl/cert.pemから非信頼ルート(eMudhra/AAA)を除去（OS更新後に再実行）
	bash scripts/macos/ca-certs.sh

doctor: ## 非信頼ルート(eMudhra/AAA)の除去と環境変数を点検（変更なし）
	bash scripts/macos/doctor.sh

doctor-online: ## doctorに加え、実サイトへ接続して各クライアントの拒否を確認
	bash scripts/macos/doctor.sh --online

##@ 個別に適用
packages: ## パッケージ導入（PROFILE=core/full、既定core）
	bash scripts/macos/brew.sh --profile "$(PROFILE)"

apply-files: ## chezmoiのファイルだけを適用（競合時は停止）
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" apply --error-on-conflict

apply-apps: ## インストール済みアプリの設定を適用（macOS）
	@if [ "$$(uname -s)" = Darwin ]; then PYTHON="$(PYTHON)" bash scripts/macos/apps.sh; fi

apply-system: ## Dock・日本語入力・電源などのシステム設定を適用（要sudo）
	bash scripts/macos/defaults.sh

runtimes: ## mise管理の言語ランタイムを導入
	mise install

shell-setup: ## zshをログインシェルに設定
	bash setup-zsh.sh

##@ 個別に確認
packages-check: ## パッケージの不足確認（PROFILE=core/full、既定core）
	bash scripts/macos/brew.sh --profile "$(PROFILE)" check

verify: ## chezmoiのファイルが宣言と一致するか確認
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" verify

check-apps: ## インストール済みアプリの設定を確認（変更なし、macOS）
	@if [ "$$(uname -s)" = Darwin ]; then PYTHON="$(PYTHON)" bash scripts/macos/apps.sh --check; fi

status: ## chezmoiの配布先ファイルの変更状況
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" status

dry-run: ## ファイル配布のプレビュー（変更なし）
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" apply --dry-run --verbose --error-on-conflict

test: ## 一時HOMEなどを使うテストを実行
	$(PYTHON) -m unittest discover -s tests -v
