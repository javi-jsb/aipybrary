.PHONY: dev migrate seed test lint

dev:
	uv run fastapi dev

migrate:
	uv run alembic upgrade head

seed:
	uv run python scripts/seed.py

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check .
