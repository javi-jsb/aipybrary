# aipybrary

*Built entirely with AI assistance as a personal learning and training project.*

A book library REST API built with Python, FastAPI, and SQLModel, backed by PostgreSQL.

## Quick start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://docs.docker.com/get-docker/) with Compose (either the `docker compose` plugin or the `docker-compose` standalone binary)

### Setup

```bash
# 1. Install Python dependencies (creates .venv, reads uv.lock)
uv sync

# 2. Install git hooks (Ruff on commit, pytest on push)
uv run pre-commit install --hook-type pre-commit --hook-type pre-push

# 3. Create your local .env from the template
cp .env.example .env
```

### Run

```bash
make db-up       # start Postgres
make db-migrate  # apply database migrations
make db-seed     # (optional) seed development data
make dev         # start the FastAPI dev server (hot reload)

# Health check
curl http://localhost:8000/health
# => {"status":"ok"}
```

### Tests and linting

```bash
make test        # run tests
make coverage    # run tests with coverage (terminal + HTML report in htmlcov/)
make check       # lint and verify formatting (no changes)
make format      # fix formatting
```

## Architecture

Each domain (e.g. `books`) follows a lightweight DDD layering:

- **domain** — entities, value objects, and the abstract repository interface
- **application** — use-case services that orchestrate domain logic
- **infrastructure** — FastAPI routers and SQLModel repository implementations

## Documentation

- `CLAUDE.md` — tech stack, commit conventions, branch naming, PR rules, dependency policy
- `openspec/changes/<change-name>/` — proposals, designs, specs, and tasks for each change
