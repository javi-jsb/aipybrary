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
# Start the FastAPI dev server (hot reload)
uv run fastapi dev

# Health check
curl http://localhost:8000/health
# => {"status":"ok"}
```

### Tests and linting

```bash
uv run pytest                          # run tests
uv run ruff format                     # format code
uv run ruff check                      # lint
```

### Database (Postgres)

```bash
docker compose up -d                   # or: docker-compose up -d
docker compose ps                      # check the container is healthy
docker compose down                    # stop and remove
```

> **Note:** Postgres is provisioned but not yet wired to the application. The next change will add SQLModel integration and the first domain entity.

## Project structure

```
aipybrary/
├── src/
│   └── app/                  # FastAPI application
│       ├── __init__.py
│       ├── config.py         # pydantic-settings (Settings class)
│       └── main.py           # FastAPI app instance + /health endpoint
├── tests/
│   └── test_health.py
├── openspec/                 # OpenSpec changes and specs (SDD)
├── docker-compose.yml        # Postgres service
├── pyproject.toml            # project metadata, dependencies, tool config
├── uv.lock                   # exact pinned dependency tree (committed)
├── .pre-commit-config.yaml   # Ruff + pytest git hooks
├── .python-version           # pinned to 3.13
├── .env.example              # template — copy to .env and adjust
├── CLAUDE.md                 # project conventions for AI-assisted development
└── README.md
```

## Documentation

- `CLAUDE.md` — tech stack, commit conventions, branch naming, PR rules, dependency policy
- `openspec/changes/<change-name>/` — proposals, designs, specs, and tasks for each change
