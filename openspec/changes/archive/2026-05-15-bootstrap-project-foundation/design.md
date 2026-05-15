## Context

The project is a greenfield Python REST API for a book library, built as a personal AI-assisted learning project. CLAUDE.md defines the tech stack and conventions, but the repository has no code, no installed dependencies, no infrastructure, and no automation in place. The next change after this one will wire SQLModel to Postgres and add the first domain entity.

This change is the first concrete code-producing change in the project and must establish the patterns that all future work will inherit.

## Goals / Non-Goals

**Goals:**
- A repo where `uv sync` + `uv run fastapi dev` boots a working FastAPI app
- A `GET /health` endpoint that proves the stack runs end-to-end
- Automated formatting, linting, and test gating before code is pushed
- Postgres available locally via `docker compose up`, even if the app does not connect to it yet
- Reproducible, supply-chain-aware dependency management
- A README that orients newcomers in under 5 minutes

**Non-Goals:**
- Database connectivity from the application (deferred to next change)
- Any domain entity or business logic
- Database migrations / Alembic
- Authentication or authorization
- CI/CD pipelines (deferred)
- Production deployment concerns
- Performance tuning or observability

## Decisions

### 1. `src/app/` layout

The Python package lives at `src/app/`, not at the repo root and not at `src/aipybrary/`.

**Why `src/` layout:** Without `src/`, the package is importable directly from the repo root because Python adds cwd to `sys.path`. This can mask packaging bugs (missing files in `pyproject.toml`, missing `__init__.py`) because tests pass locally via cwd resolution but fail in installed environments. The `src/` layout forces all imports through the installed package, surfacing these bugs immediately.

**Why `src/app/` instead of `src/aipybrary/`:** The repo is already named `aipybrary`. Repeating the name (`src/aipybrary/`) creates redundancy with no functional benefit for an internal application (not a library to publish). Using `app` keeps imports short (`from app.main import api`) and unambiguous.

**Alternatives considered:**
- Flat layout (`app/` at repo root) — rejected: loses the import isolation benefit
- `src/library/` — rejected: "library" in software is ambiguous (codebase library vs. book library) and can read confusingly in imports
- Multiple top-level packages under `src/` (`src/api/`, `src/core/`, etc.) — rejected: short generic names collide with PyPI packages and break the standard `src/<package>/` convention

### 2. Dependency pinning policy

Direct dependencies declared in `pyproject.toml` use exact pins (`==X.Y.Z`). The lockfile `uv.lock` is committed and pins transitive dependencies plus SHA256 hashes. Upgrades happen only via explicit `uv add "pkg==X.Y.Z"` (or editing `pyproject.toml` and running `uv sync`).

**Why exact pins on direct deps:** Two protections combine. The lockfile protects between resolutions. Exact pins on direct deps protect the resolution moment itself: when `pyproject.toml` changes and `uv sync` re-resolves, the range cannot drift to a newly published (potentially malicious) version. Each top-level version change is recorded as a visible diff in `pyproject.toml`, not buried in `uv.lock`.

**Why also commit `uv.lock`:** PyPI artifacts per version are immutable, but transitive dependencies still resolve within ranges declared by upstream packages. Without the lockfile, transitives could drift to malicious or breaking versions on any resolution. The lockfile freezes the entire dependency tree with hashes.

**Operational rules:**
- `uv sync` for local dev (installs from lockfile when consistent; re-resolves only when `pyproject.toml` changes)
- `uv sync --frozen` in automated environments (forbids implicit resolution)
- Any PR touching `pyproject.toml` or `uv.lock` requires explicit review of the dependency diff

**Alternatives considered:**
- Range pins on direct deps + lockfile (`>=0.115,<0.116`) — rejected for explicit-control preference: changes show up only in lockfile, not in `pyproject.toml`
- No lockfile — rejected: zero supply-chain protection on transitives

### 3. Health endpoint as the first observable behavior

The application exposes a single `GET /health` endpoint returning `{"status": "ok"}`. This is the simplest possible end-to-end smoke: it proves FastAPI starts, the route is registered, the test client works, and the dev server is reachable.

**Why not nothing:** A FastAPI app with no endpoints has no testable surface, so the test suite would be empty and we would not know whether the stack actually works.

**Why not more (e.g., DB connectivity check):** The application does not connect to Postgres in this change. A health endpoint that pings the DB belongs in the next change, alongside SQLModel wiring.

### 4. `pydantic-settings` scaffolding from day one

`pydantic-settings` is installed and a minimal `Settings` class is created in `src/app/config.py`, even though there are no real settings to read yet. `.env.example` is committed; `.env` is gitignored.

**Why introduce it before it is needed:** Settings management is a pattern that every future feature touches (DB URL, secrets, feature flags). Setting it up now means subsequent changes add to an established pattern rather than retrofitting one mid-project.

### 5. Pre-commit framework over native git hooks

Git hooks are managed via the `pre-commit` Python framework (`.pre-commit-config.yaml`), not by versioning shell scripts in `.githooks/`.

**Why `pre-commit`:** Versioned config in the repo, automatic tool version management, only runs on changed files, de facto standard in the Python ecosystem.

**Hook layout:**
- `pre-commit` stage: `ruff format --check` and `ruff check` — fast, fail before commit
- `pre-push` stage: `pytest` — slower, fail before push

**Setup requirement:** After cloning, developers run `pre-commit install --hook-type pre-commit --hook-type pre-push`. This is documented in the README.

**Alternatives considered:**
- Native `.githooks/` shell scripts + `git config core.hooksPath` — rejected: requires manual config in each clone, more code to maintain, no built-in tool version pinning
- Single `pre-commit` stage running pytest too — rejected: slow tests on every commit discourage frequent commits

### 6. Docker compose for Postgres, but no application wiring

`docker-compose.yml` defines a single `postgres` service with a persisted volume and reasonable defaults. The application does not import any DB driver, does not configure SQLModel, and does not open a connection.

**Why include Postgres now:** Having `docker compose up -d` work from day one means the next change (DB wiring) doesn't need to set up infrastructure — it only needs to add code. This isolates each PR to one concern at a time.

**Why not wire the app to it:** Wiring SQLModel sessions without any entity to persist creates dead code. Connection + sessions + first entity should land together where they have a purpose.

**Alternatives considered:**
- Postgres + minimal SQLModel engine setup now, entities later — rejected: leaves engine code untested and unused
- Defer Docker entirely to a later change — rejected: makes the next change larger and mixes infra setup with feature work

### 7. README tone and content

The README opens with an italic disclaimer:

> *Built entirely with AI assistance as a personal learning and training project.*

Then provides: short description, quick start (install with uv, run dev server, run tests, start Postgres), and project structure overview. No marketing tone, no roadmaps.

## Risks / Trade-offs

- **`src/app/` adds a directory level for a single package** → Accepted in exchange for import isolation. Documented here so the choice is not revisited later.
- **Exact-pin policy adds friction to upgrades** → Accepted: every upgrade is an intentional, reviewable act. Aligns with the project's learning goal of understanding what is being installed.
- **Pre-commit framework adds a setup step (`pre-commit install`)** → Mitigated by documenting it in README. Skipped hooks would not block anything else (there is no CI yet), so the hook is the only gate.
- **Postgres in `docker-compose.yml` but unused** → Could confuse readers expecting the app to talk to it. Mitigated by README explicitly noting it is "ready for the next change."
- **`sqlmodel` declared but not imported** → Slight noise in `pyproject.toml`. Mitigated by the fact that the next change will use it immediately; declaring it now keeps the foundation PR self-contained for tooling.
- **No CI means hooks are the only enforcement** → Accepted: hooks run locally, pre-push catches test failures before remote. CI will be added in a later change.

## Migration Plan

Not applicable — this is a greenfield change. No existing data or APIs to migrate.

## Open Questions

- **Specific dependency versions to pin** — decided at implementation time using the latest stable versions available when running `uv add`. Captured in `pyproject.toml` and `uv.lock` at that moment.
- **Postgres version in `docker-compose.yml`** — use the latest stable Postgres major release (currently 17) with an explicit major-version tag (`postgres:17`), not `latest`.
