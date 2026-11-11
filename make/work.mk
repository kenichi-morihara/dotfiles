##@ 仕事用ツール（明示的に導入）
.PHONY: pi-setup
pi-setup: ## 会社用: pi を導入
	bash modules/pi-work-config/scripts/install.sh

.PHONY: claude-admin-setup claude-admin-default
claude-admin-setup: ## 会社用: 管理者向け Claude ランチャーを導入
	$(PYTHON) modules/claude-work-tools/scripts/install.py

claude-admin-default: ## 会社用: この端末の通常の claude に管理者設定を登録
	$(PYTHON) modules/claude-work-tools/scripts/install.py --default
