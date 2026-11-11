.PHONY: test test-vscode preview-vscode

##@ 開発とテスト
test: ## 一時HOMEなどを使うテストを実行
	$(PYTHON) scripts/test-modules.py

test-vscode: ## 実VS Code+ruby-lspでDark Modern Roseの色を確認（VS Codeを一時起動）
	node modules/dark-modern-rose/tests/vscode_theme/e2e.mjs

preview-vscode: ## Dark Modern Roseの色をターミナルで即確認（FILE=... で対象指定、保存で自動再描画）
	$(PYTHON) modules/dark-modern-rose/tests/vscode_theme/preview.py -w $(FILE)

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
	$(PYTHON) scripts/common/rollback.py restore --run "$$DOTFILES_ROLLBACK_RUN" --target "$$DOTFILES_ROLLBACK_TARGET"
