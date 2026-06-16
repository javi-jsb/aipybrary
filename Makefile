.DEFAULT_GOAL := help
.PHONY: help dev db-migrate db-seed test coverage check format db-up db-down db-down-clean

##@ Dev
dev: ## Run the FastAPI dev server
	uv run fastapi dev

##@ Database
db-up: ## Start PostgreSQL via Docker
	docker compose up -d

db-down: ## Stop and remove the Docker containers
	docker compose down

db-down-clean: ## Stop and remove the Docker containers and volumes
	docker compose down -v

db-migrate: ## Apply Alembic migrations (upgrade head)
	uv run alembic upgrade head

db-seed: ## Seed the database with sample data
	uv run python scripts/seed.py

##@ Testing
test: ## Run the test suite
	uv run pytest

coverage: ## Run tests with coverage (terminal + HTML report)
	uv run pytest --cov --cov-report=term-missing --cov-report=html

##@ Code quality
check: ## Lint and verify formatting (no changes)
	uv run ruff check . && uv run ruff format --check .

format: ## Auto-format the codebase
	uv run ruff format .

##@ Help
help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)
