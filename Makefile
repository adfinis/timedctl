.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort -k 1,1 | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint: ## Lint the code
	@poetry run sh -c "ruff format --check . ; ruff check ."

.PHONY: lint-fix
lint-fix: ## Lint and fix code
	@poetry run sh -c "ruff format . && ruff check . --fix"

.PHONY: test
test: ## Test the code
	@poetry run pytest --no-cov-on-fail --cov -vvv -s

