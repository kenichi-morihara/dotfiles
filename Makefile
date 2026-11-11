.DEFAULT_GOAL := help

SHELL := /bin/bash
ROOT := $(shell pwd)
CHEZMOI ?= chezmoi
PYTHON ?= python3
export DOTFILES_PROFILE_PYTHON := $(PYTHON)
PROFILE ?=
PROFILE_TOOL = $(PYTHON) scripts/common/profiles.py
PROFILE_STATE = $(if $(XDG_CONFIG_HOME),$(XDG_CONFIG_HOME),$(HOME)/.config)/dotfiles/profile

.PHONY: help setup init apply check diff dry-run status \
	apply-files apply-apps apply-system verify check-apps \
	macos-init sudo-touchid packages packages-check runtimes shell-setup test

help: ## 操作一覧（既定）
	@awk 'BEGIN {FS = ":.*## "} /^##@ / {printf "\n%s\n", substr($$0, 5)} /^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' Makefile

##@ 普段使う操作
setup: ## 選択中profileのパッケージ・設定・ランタイム・repoを導入
	$(PROFILE_TOOL) setup $(if $(PROFILE),--package-profile "$(PROFILE)")

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

##@ 個別に適用
packages: ## パッケージ導入（PROFILE=core/full、既定core）
	@if [ -f "$(PROFILE_STATE)" ]; then $(PROFILE_TOOL) packages $(if $(PROFILE),--package-profile "$(PROFILE)"); else bash scripts/macos/brew.sh --profile "$(or $(PROFILE),core)"; fi

apply-files: ## chezmoiのファイルだけを適用（競合時は停止）
	@echo '==> Files (chezmoi)'
	@changes="$$($(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" status)" || exit $$?; \
	if [ -z "$$changes" ]; then \
		echo '    変更なし'; \
	else \
		echo '    適用する変更（A=追加 M=変更 D=削除 R=スクリプト実行）:'; \
		printf '%s\n' "$$changes" | sed 's/^/    /'; \
	fi
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" apply --error-on-conflict

apply-apps: ## インストール済みアプリの設定を適用（macOS）
	@if [ "$$(uname -s)" = Darwin ]; then echo '==> Apps (macOS)'; PYTHON="$(PYTHON)" bash scripts/macos/apps.sh; fi

apply-system: ## Dock・日本語入力・電源などのシステム設定を適用（要sudo）
	bash scripts/macos/defaults.sh

runtimes: ## mise管理の言語ランタイムを導入
	mise install

shell-setup: ## zshをログインシェルに設定
	bash setup-zsh.sh

##@ 個別に確認
packages-check: ## パッケージの不足確認（PROFILE=core/full、既定core）
	@if [ -f "$(PROFILE_STATE)" ]; then $(PROFILE_TOOL) packages --check $(if $(PROFILE),--package-profile "$(PROFILE)"); else bash scripts/macos/brew.sh --profile "$(or $(PROFILE),core)" check; fi

verify: ## chezmoiのファイルが宣言と一致するか確認
	@$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" verify || { \
		result=$$?; \
		echo 'File verification failed. Pending changes (current -> declared):' >&2; \
		$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" --no-pager diff; \
		echo 'Review with make diff; apply with make apply-files.' >&2; \
		exit $$result; \
	}

check-apps: ## インストール済みアプリの設定を確認（変更なし、macOS）
	@if [ "$$(uname -s)" = Darwin ]; then PYTHON="$(PYTHON)" bash scripts/macos/apps.sh --check; fi

status: ## chezmoiの配布先ファイルの変更状況
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" status

dry-run: ## ファイル配布のプレビュー（変更なし）
	$(CHEZMOI) --source "$(ROOT)" --destination "$(HOME)" apply --dry-run --verbose --error-on-conflict

test: ## 一時HOMEなどを使うテストを実行
	$(PYTHON) -m unittest discover -s tests -v

export DOTFILES_ROLLBACK_ACTION := $(ACTION)
export DOTFILES_ROLLBACK_RUN := $(RUN)
export DOTFILES_ROLLBACK_TARGET := $(TARGET)

##@ 適用履歴と復元
.PHONY: tracked rollback-legacy rollback-plan rollback
tracked: ## 適用前後を記録して実行（ACTION=setup、apply、apply-system など）
	$(PYTHON) scripts/common/rollback.py track --action "$$DOTFILES_ROLLBACK_ACTION" --chezmoi "$(CHEZMOI)" --profile "$(PROFILE)"

rollback-legacy: ## 既存のバックアップ候補を表示（変更なし）
	$(PYTHON) scripts/common/rollback.py legacy --chezmoi "$(CHEZMOI)"

rollback-plan: ## 指定した実行の復元予定を表示（RUN=実行ID、変更なし）
	$(PYTHON) scripts/common/rollback.py plan --run "$$DOTFILES_ROLLBACK_RUN"

rollback: ## 指定した実行で変更したファイルを復元（RUN=実行ID、TARGETで1件指定可）
	$(PYTHON) scripts/common/rollback.py restore --run "$$DOTFILES_ROLLBACK_RUN" --target "$$DOTFILES_ROLLBACK_TARGET" --chezmoi "$(CHEZMOI)"

##@ 用途・端末別profile
.PHONY: profile-select profile-show setup-plan repos
profile-select: ## 用途・端末のprofileを保存（NAME=personal または work/<端末ID>）
	$(PROFILE_TOOL) select --name "$(NAME)"

profile-show: ## 選択中profileの実効設定を表示
	$(PROFILE_TOOL) show

setup-plan: ## 一括導入の予定を表示（変更なし）
	$(PROFILE_TOOL) plan

repos: ## 選択中profileのrepo取得・開発依存導入
	$(PROFILE_TOOL) repos
