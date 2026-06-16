# aipybrary

Book library REST API built with Python, FastAPI, and SQLModel.

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.13 |
| Framework | FastAPI (`fastapi[standard]`) |
| ORM | SQLModel |
| Database | PostgreSQL (Docker for local dev) |
| Package manager | uv |
| Linting & formatting | Ruff |
| Testing | pytest + pytest-asyncio + pytest-cov |

## Development Conventions

### Commits — Conventional Commits

```
<type>(<optional scope>): <short description>
```

| Type | When |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Maintenance (deps, config, tooling) |
| `refactor` | Code restructuring without behavior change |
| `docs` | Documentation only |
| `test` | Tests only |

### Branch naming

```
<type>/<issue-number>-<short-description>
```

Examples: `feat/5-add-book-endpoint`, `fix/12-null-author-crash`, `chore/1-create-claude-md`

### Commit granularity

Commits within a PR must be grouped by logical section, not bundled into a single monolithic commit. Each commit should represent a cohesive unit of work (e.g., dependencies, domain layer, infrastructure, tests). This makes the PR easier to review commit-by-commit.

### Pull Requests

- Every PR must reference its issue with `Closes #N` **in the PR body**, not in individual commits — the close trigger fires on squash merge via the PR description
- PR title follows the same Conventional Commits format as the branch
- Merge strategy: **squash merge** — keeps `main` history linear; GitHub uses the PR title as the resulting commit message
- After merging, always pull `main` locally and delete the merged branch:
  ```bash
  git checkout main && git pull origin main && git branch -d <branch>
  ```

### Dependencies

Pinning policy:

- All direct dependencies in `pyproject.toml` use exact version pins (`package==X.Y.Z`), both runtime and dev
- `uv.lock` is committed; it pins transitive dependencies and SHA256 hashes
- Upgrades are deliberate: `uv add "package==X.Y.Z"` or edit `pyproject.toml` and run `uv sync`
- Every PR that modifies `pyproject.toml` or `uv.lock` must have its dependency diff reviewed explicitly before merge
- In automated environments (CI, prod, once they exist), use `uv sync --frozen` so resolution is forbidden

### Development commands

All commands go through the Makefile — never call `uv run ...` directly.

**Dev**
- `make dev` — start the FastAPI development server

**Database**
- `make db-up` — start PostgreSQL via Docker Compose
- `make db-down` — stop and remove Docker containers
- `make db-migrate` — apply Alembic migrations (`upgrade head`)
- `make db-seed` — seed the database with sample data

**Testing**
- `make test` — run the test suite
- `make coverage` — run tests with coverage; produces a terminal report (missing lines) and an HTML report in `htmlcov/`

**Code quality**
- `make check` — lint and format verification (read-only)
- `make format` — auto-format the codebase

Coverage target: tests should aim for close to 100%. Use `# pragma: no cover` only for genuinely untestable lines — abstract method stubs and dependency-injection wiring that is replaced in tests.

Note: the `db_setup` fixture in `tests/conftest.py` runs Alembic migrations automatically before each test (`upgrade head`) and rolls them back after (`downgrade base`). No explicit migration step is needed in CI.

### OpenSpec workflow

OpenSpec changes live under `openspec/changes/<change-name>/` while active. Once a change is complete (all tasks done, all artifacts marked done), it must be **archived through its own dedicated issue + PR** — never folded into the implementation PR, never a direct commit to `main`.

Archive issue/branch/PR convention:

- Issue title: `chore(openspec): archive '<change-name>' change`
- Branch: `chore/<N>-archive-<change-name>`
- The PR syncs each delta spec into `openspec/specs/<capability>/spec.md` and moves the change directory to `openspec/changes/archive/YYYY-MM-DD-<change-name>/`.

## Architecture

### Slice-per-domain layout

Each domain lives under `src/app/<domain>/` with three sub-packages:

| Sub-package | Contents |
|---|---|
| `domain/` | Models, repository interface (ABC), exceptions, value objects |
| `application/` | Service classes — orchestrate domain objects, own transactions |
| `infrastructure/` | SQLModel repository implementation, FastAPI router |

Cross-slice infrastructure imports (e.g., `sql_member_repository` importing `User`) are allowed when a foreign-key relationship requires a join. Domain layers must not import from sibling slices.

`app/core/` is a leaf module — no slice imports allowed from within it. Shared field-validation rules that any slice's DTOs may need (e.g. `validate_email` in `app/core/validators.py`) live here so the rule has a single owner and cannot diverge between slices.

### Authentication and auth gate

All routes except `GET /health`, `POST /auth/login`, and FastAPI's auto-generated documentation endpoints (`/docs`, `/redoc`, `/openapi.json`) require a valid JWT bearer token. The documentation endpoints are mounted directly on the `app` instance rather than on a router, so the `_auth_gate` dependency does not apply to them. The dependency `get_current_user` (in `app/users/infrastructure/auth_router.py`) validates the token and resolves the caller to a `User` object. Integration tests bypass this via `app.dependency_overrides[get_current_user]` in `tests/conftest.py`.

Endpoints:
- `POST /auth/login` — accepts OAuth2 form credentials, returns `{"access_token": "...", "token_type": "bearer"}`
- `GET /auth/me` — returns the authenticated user's profile

JWT settings (all required):

| Variable | Description |
|---|---|
| `JWT_SECRET` | Signing secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | Default `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Default `30` |

### users/ slice

`User` stores credentials and role for every person who can call the API. Roles: `admin`, `staff`, `member`.

`UserRole` is a `StrEnum`. When read back from PostgreSQL, the value is a plain `str` — comparing with `UserRole.member` (not `.value`) works because `StrEnum.__eq__` compares by value.

### members/ slice

`Member` no longer holds an email column. Email is owned by the linked `User` (via `member.user_id` FK). Operations that need email (list, get, update) return `tuple[Member, str]` from the repository. `LoanService` calls `get_by_id` (no email needed) to avoid the join overhead.

`POST /members` provisions a linked `member`-role `User`, sets a random initial password, and returns it once in `MemberCreateResponse.initial_password`. Subsequent reads omit it.

### Test fixtures

`tests/conftest.py` provides two HTTP client fixtures:

| Fixture | Auth behaviour |
|---|---|
| `client` | Overrides `get_current_user` with a fake staff user — use for all non-auth feature tests |
| `auth_client` | No override — use for testing real login / token validation flows |

## Language

All public-facing content must be written in **English**: issues, PR titles and descriptions, commit messages, code, comments, and documentation.

## AI Collaboration Rules

**Debate before executing.** If something seems wrong, missing, inconsistent, or improvable, raise it and discuss options before proceeding. Do not execute blindly.

**Keep this file up to date.** If during development a decision is made, a convention is added, or anything worth documenting changes, update `CLAUDE.md` accordingly in the same PR where the change happens.
