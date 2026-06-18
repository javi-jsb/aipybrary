.DEFAULT_GOAL := help
.PHONY: help dev dev-frontend db-migrate db-seed test coverage test-frontend coverage-frontend e2e-setup e2e-frontend e2e-api db-e2e-provision db-e2e-reset check format db-up db-down db-down-clean

# Dedicated E2E database, API port, and SPA port — kept off the dev defaults
# (8077 / 5173) so the E2E stack never collides with a running `make dev` /
# `make dev-frontend`.
E2E_DB ?= aipybrary_e2e
E2E_API_PORT ?= 8078
E2E_APP_PORT ?= 5273

##@ Dev
dev: ## Run the FastAPI dev server
	uv run fastapi dev --port 8077

dev-frontend: ## Run the frontend dev server (Vite) from /frontend
	pnpm --dir frontend dev

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

test-frontend: ## Run the frontend test suite (Vitest) from /frontend
	pnpm --dir frontend test

coverage-frontend: ## Run frontend tests with coverage (terminal + HTML report)
	pnpm --dir frontend coverage

e2e-setup: ## One-time E2E setup: install frontend deps + the Chromium browser
	pnpm --dir frontend install
	pnpm --dir frontend exec playwright install chromium

e2e-frontend: ## Run the end-to-end test suite (Playwright) from /frontend
	pnpm --dir frontend test:e2e

e2e-api: ## Run the FastAPI server against the E2E database (used by Playwright's webServer)
	POSTGRES_DB=$(E2E_DB) CORS_ALLOW_ORIGINS=http://localhost:$(E2E_APP_PORT) uv run fastapi dev --port $(E2E_API_PORT)

db-e2e-provision: ## Create + migrate + seed the dedicated E2E database
	POSTGRES_DB=$(E2E_DB) uv run python scripts/e2e_db.py provision

db-e2e-reset: ## Truncate + re-seed the E2E database (between-spec reset)
	POSTGRES_DB=$(E2E_DB) uv run python scripts/e2e_db.py reset

##@ Code quality
check: ## Lint and verify formatting (no changes)
	uv run ruff check . && uv run ruff format --check .

format: ## Auto-format the codebase
	uv run ruff format .

##@ Help
help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)
