# aipybrary

[![CI](https://github.com/javi-jsb/aipybrary/actions/workflows/ci.yml/badge.svg)](https://github.com/javi-jsb/aipybrary/actions/workflows/ci.yml)
[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/javi-jsb/36ba6bf5a954d5bafa0aa417b0100ba8/raw/aipybrary-coverage.json)](https://github.com/javi-jsb/aipybrary/actions/workflows/ci.yml)

*Built entirely with AI assistance as a personal learning and training project.*

A book library application: a Python/FastAPI/SQLModel REST API (backed by PostgreSQL) plus a React + TypeScript + Tailwind single-page frontend under `/frontend`.

## Quick start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://docs.docker.com/get-docker/) with Compose (either the `docker compose` plugin or the `docker-compose` standalone binary)
- [Node.js](https://nodejs.org/) + [pnpm](https://pnpm.io/) — only for the `/frontend` SPA

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

**Backend** (API on `:8077`):

```bash
make db-up       # start Postgres
make db-migrate  # apply database migrations
make db-seed     # (optional) seed development data
make dev         # start the FastAPI dev server (hot reload)

# Health check
curl http://localhost:8077/health
# => {"status":"ok"}
```

**Frontend** (Vite dev server on `:5173`):

```bash
pnpm --dir frontend install   # first time only
make dev-frontend             # start the SPA (calls the API at :8077)
```

See `frontend/README.md` for frontend details and the `VITE_API_BASE_URL` setting.

### Tests and linting

```bash
make test        # run tests
make coverage    # run tests with coverage (terminal + HTML report in htmlcov/)
make check       # lint and verify formatting (no changes)
make format      # fix formatting
```

## Architecture

The backend lives at the repo root; the browser SPA is a self-contained app under `/frontend` (React + TS + Tailwind via Vite) that calls the API through a shared `apiClient`.

On the backend, each domain (e.g. `books`) follows a lightweight DDD layering:

- **domain** — entities, value objects, and the abstract repository interface
- **application** — use-case services that orchestrate domain logic
- **infrastructure** — FastAPI routers and SQLModel repository implementations

## Documentation

- `CLAUDE.md` — tech stack, commit conventions, branch naming, PR rules, dependency policy
- `frontend/README.md` — frontend setup, stack, and commands
- `openspec/changes/<change-name>/` — proposals, designs, specs, and tasks for each change
