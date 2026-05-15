## Why

The project has tooling conventions defined in CLAUDE.md but no actual code, dependencies, or infrastructure in place. Before any feature work can begin, the repository needs a runnable Python application, a configured dev toolchain, and the Postgres infrastructure ready to use. This change establishes that foundation in one coherent step so subsequent issues can focus on real domain features (entities, database integration, endpoints).

## What Changes

- Add Python project scaffolding with `uv` and `pyproject.toml`, pinning Python 3.13 via `.python-version`
- Adopt a `src/app/` layout to enforce import isolation (the package is not implicitly importable from the repo root)
- Create a minimal FastAPI application exposing `GET /health` to verify the stack boots end-to-end
- Add `pydantic-settings` + `.env` / `.env.example` scaffolding to establish the configuration pattern
- Configure Ruff for formatting and linting, wired into a `pre-commit` framework with two hooks:
  - `pre-commit`: Ruff format + Ruff check
  - `pre-push`: pytest
- Add a `docker-compose.yml` defining a Postgres service ready to run, **without wiring it to the application yet**
- Add `tests/` with a smoke test for `/health` using pytest + pytest-asyncio + httpx
- Add a `README.md` with project description (including AI-assisted learning disclaimer), quick start, and structure overview
- Declare `sqlmodel` as a dependency in advance, even though it is not used in code in this change
- Adopt an exact-pin dependency policy: direct dependencies in `pyproject.toml` use `==X.Y.Z`, `uv.lock` is committed, upgrades are deliberate
- Update `CLAUDE.md` with a new "Dependencies" convention section documenting the pinning policy
- Version the official FastAPI Claude Code skill at `.claude/skills/fastapi/` so AI-assisted FastAPI work shares the same guidance across contributors

## Capabilities

### New Capabilities

- `health-check`: The application exposes an HTTP endpoint that reports whether the service is up, so external systems (and humans) can verify the deployment is alive.

### Modified Capabilities

_None — this is the first change; no prior specs exist._

## Impact

- **New files**: `pyproject.toml`, `.python-version`, `.env.example`, `.pre-commit-config.yaml`, `docker-compose.yml`, `README.md`, `src/app/__init__.py`, `src/app/main.py`, `tests/__init__.py`, `tests/test_health.py`, `uv.lock`, `.claude/skills/fastapi/**`
- **Modified files**: `CLAUDE.md` (new "Dependencies" subsection)
- **Dependencies introduced**: `fastapi[standard]`, `sqlmodel`, `pydantic-settings`; dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `pre-commit`
- **Local dev workflow**: developers must run `uv sync` and `pre-commit install --hook-type pre-commit --hook-type pre-push` after cloning; running Postgres requires `docker compose up -d`
- **No runtime DB dependency yet**: the app starts and serves `/health` without Postgres being up
- **No CI yet**: GitHub Actions is explicitly deferred to a later change
