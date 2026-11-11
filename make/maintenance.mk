.PHONY: test

##@ テスト
test: ## 一時HOMEなどを使うテストを実行
	$(PYTHON) -m unittest discover -s tests -v
