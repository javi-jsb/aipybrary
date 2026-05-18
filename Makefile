.PHONY: dev migrate seed test coverage lint

dev:
	uv run fastapi dev

migrate:
	uv run alembic upgrade head

seed:
	uv run python scripts/seed.py

test:
	uv run pytest

coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check . && uv run ruff format --check .
