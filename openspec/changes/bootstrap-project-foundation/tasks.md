## 1. Project initialization

- [x] 1.1 Initialize the project with `uv init --package --name aipybrary --src` (or equivalent), producing `pyproject.toml`, source skeleton, and placeholders
- [x] 1.2 Rename the generated package directory to `src/app/` and update `pyproject.toml` package configuration accordingly
- [x] 1.3 Create `.python-version` containing `3.13`
- [x] 1.4 Update `pyproject.toml` metadata: `description`, `requires-python = ">=3.13,<3.14"`, license, authors
- [x] 1.5 Extend `.gitignore` with Python/uv artifacts if not already present (`.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `.env`)

## 2. Dependencies (exact-pin policy)

- [x] 2.1 Add runtime dependencies with explicit `==` pins: `uv add "fastapi[standard]==<latest>" "sqlmodel==<latest>" "pydantic-settings==<latest>"`
- [x] 2.2 Add dev dependencies with explicit `==` pins: `uv add --dev "pytest==<latest>" "pytest-asyncio==<latest>" "httpx==<latest>" "ruff==<latest>" "pre-commit==<latest>"`
- [x] 2.3 Verify `uv.lock` is generated and committed, and that `uv sync --frozen` completes cleanly

## 3. Application code

- [x] 3.1 Create `src/app/__init__.py` (empty marker file)
- [x] 3.2 Create `src/app/config.py` with a minimal `Settings(BaseSettings)` class reading from `.env`
- [x] 3.3 Create `src/app/main.py`: instantiate `FastAPI`, define `GET /health` returning `{"status": "ok"}`

## 4. Tests

- [x] 4.1 Create `tests/__init__.py` (empty)
- [x] 4.2 Configure pytest in `pyproject.toml`: `[tool.pytest.ini_options]` with test paths, asyncio mode
- [x] 4.3 Create `tests/test_health.py` with an httpx-based test asserting `GET /health` returns `200` and `{"status": "ok"}`. The same test implicitly covers the "independent of external services" scenario because no external systems are needed for it to pass
- [x] 4.4 Run `uv run pytest` and verify green

## 5. Ruff configuration

- [x] 5.1 Add `[tool.ruff]` and `[tool.ruff.lint]` sections to `pyproject.toml` with sensible defaults (line length, target Python version, lint rule selection)
- [x] 5.2 Run `uv run ruff format` and `uv run ruff check --fix` to bring the codebase to a clean state

## 6. Pre-commit hooks

- [x] 6.1 Create `.pre-commit-config.yaml` with two stages:
      - `pre-commit`: Ruff format check and Ruff lint check
      - `pre-push`: pytest
- [x] 6.2 Install hooks locally: `pre-commit install --hook-type pre-commit --hook-type pre-push`
- [x] 6.3 Verify hooks fire: make a trivial dirty change and confirm `git commit` is blocked

## 7. Configuration scaffolding (.env)

- [x] 7.1 Create `.env.example` with placeholder Postgres variables (`POSTGRES_*`) — declared for the next change but not read by the app yet
- [x] 7.2 Confirm `.env` is in `.gitignore`

## 8. Docker / Postgres

- [x] 8.1 Create `docker-compose.yml` with a single `postgres:17` service: persisted named volume, port 5432 exposed, env variables sourced from `.env`
- [x] 8.2 Verify the service starts: `docker compose up -d`, `docker compose ps` shows running, then `docker compose down`

## 9. Documentation

- [x] 9.1 Write `README.md`:
      - Italic disclaimer at the top: *"Built entirely with AI assistance as a personal learning and training project."*
      - Short project description
      - Quick start: prerequisites (`uv`, Docker), `uv sync`, `pre-commit install --hook-type pre-commit --hook-type pre-push`, `uv run fastapi dev`, `uv run pytest`, `docker compose up -d`
      - Project structure tree
      - Explicit note that Postgres is provided but not yet connected to the app
- [x] 9.2 Add a new "Dependencies" subsection to `CLAUDE.md` under "Development Conventions" describing the exact-pin policy, the committed lockfile, and the upgrade workflow

## 10. Final verification

- [x] 10.1 Fresh-install simulation: remove `.venv`, run `uv sync`; verify it completes without errors
- [x] 10.2 Boot the app: `uv run fastapi dev src/app/main.py`; hit `GET /health` and confirm `{"status": "ok"}`
- [x] 10.3 Run the test suite: `uv run pytest` (all green)
- [x] 10.4 Run linting: `uv run ruff format --check && uv run ruff check` (no findings)
- [x] 10.5 Start Postgres: `docker compose up -d`; confirm container is `running`; `docker compose down`

## 11. AI development tooling

- [x] 11.1 Add the official FastAPI Claude Code skill under `.claude/skills/fastapi/` (drop-in: presence in the directory is enough, no install step required)
- [x] 11.2 Verify the skill is picked up by Claude Code (visible in `/skills`) on a fresh session

## 12. FastAPI CLI entrypoint

- [x] 12.1 Add `[tool.fastapi]` section to `pyproject.toml` with `entrypoint = "app.main:app"` so the FastAPI CLI finds the app automatically
- [x] 12.2 Simplify the README "Run" command from `uv run fastapi dev src/app/main.py` to `uv run fastapi dev`
- [x] 12.3 Verify `uv run fastapi dev` boots the app and `GET /health` returns `{"status": "ok"}`
