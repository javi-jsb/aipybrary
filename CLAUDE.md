# aipybrary

Book library project: a FastAPI + SQLModel backend and a React SPA frontend that exercises it. Monorepo — the backend lives at the repo root, the frontend under `/frontend`.

## Repository layout

| Path | What |
|---|---|
| `src/app/` | Backend (FastAPI, SQLModel), sliced per domain |
| `tests/` | Backend tests (pytest) |
| `Makefile`, `pyproject.toml`, `uv.lock` | Backend tooling — **backend-only** |
| `frontend/` | Self-contained React SPA (its own Node toolchain) |
| `openspec/` | OpenSpec changes and specs |

## Conventions (shared)

These apply to the whole repo, backend and frontend alike.

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

Example: `feat/5-add-book-endpoint`

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

### OpenSpec workflow

OpenSpec changes live under `openspec/changes/<change-name>/` while active. Once a change is complete (all tasks done, all artifacts marked done), it must be **archived through its own dedicated issue + PR** — never folded into the implementation PR, never a direct commit to `main`.

Archive issue/branch/PR convention:

- Issue title: `chore(openspec): archive '<change-name>' change`
- Branch: `chore/<N>-archive-<change-name>`
- The PR syncs each delta spec into `openspec/specs/<capability>/spec.md` and moves the change directory to `openspec/changes/archive/YYYY-MM-DD-<change-name>/`.

### Git hooks

`.pre-commit-config.yaml` guards both stacks, scoped by path so backend-only commits never spin up Node and vice versa:

| Stage | Backend | Frontend (`frontend/` files) |
|---|---|---|
| `pre-commit` (fast) | `ruff-format`, `ruff` | `frontend-lint` (ESLint), `frontend-format` (Prettier `--check`) |
| `pre-push` (slower) | `pytest` | `frontend-typecheck` (`tsc -b`), `frontend-test` (Vitest) |

The frontend hooks run the existing pnpm scripts, so **Node + pnpm must be installed**. Install the hooks once with `uv run pre-commit install` (or `pre-commit install`).

### Language

All public-facing content must be written in **English**: issues, PR titles and descriptions, commit messages, code, comments, and documentation.

## Backend

### Stack

| Layer | Choice |
|---|---|
| Language | Python 3.13 |
| Framework | FastAPI (`fastapi[standard]`) |
| ORM | SQLModel |
| Database | PostgreSQL (Docker for local dev) |
| Package manager | uv |
| Linting & formatting | Ruff |
| Testing | pytest + pytest-asyncio + pytest-cov |

### Commands

All backend commands go through the Makefile — never call `uv run ...` directly. Run `make help` (or read the `Makefile`) for the full target list. Non-obvious point worth knowing:

- `make dev` serves on port `8077`, not the conventional `8000`, which commonly collides with Docker/Colima port forwards. `VITE_API_BASE_URL` must match.

### Dependencies

Pinning policy (backend; for the frontend analog see the Frontend section):

- All direct dependencies in `pyproject.toml` use exact version pins (`package==X.Y.Z`), both runtime and dev
- `uv.lock` is committed; it pins transitive dependencies and SHA256 hashes
- Upgrades are deliberate: `uv add "package==X.Y.Z"` or edit `pyproject.toml` and run `uv sync`
- Every PR that modifies `pyproject.toml` or `uv.lock` must have its dependency diff reviewed explicitly before merge
- In automated environments (CI, prod, once they exist), use `uv sync --frozen` so resolution is forbidden

### Architecture

#### Slice-per-domain layout

Each domain lives under `src/app/<domain>/` with three sub-packages:

| Sub-package | Contents |
|---|---|
| `domain/` | Models, repository interface (ABC), exceptions, value objects |
| `application/` | Service classes — orchestrate domain objects, own transactions |
| `infrastructure/` | SQLModel repository implementation, FastAPI router |

Cross-slice infrastructure imports (e.g., `sql_member_repository` importing `User`) are allowed when a foreign-key relationship requires a join. Domain layers must not import from sibling slices.

`app/core/` is a leaf module — no slice imports allowed from within it. Shared field-validation rules that any slice's DTOs may need (e.g. `validate_email` in `app/core/validators.py`) live here so the rule has a single owner and cannot diverge between slices.

#### Authentication and auth gate

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

#### CORS

The frontend SPA calls the API directly cross-origin (browser at the Vite dev origin → FastAPI at `http://localhost:8077`), so `CORSMiddleware` is registered in `app/main.py`. Allowed origins come from the `CORS_ALLOW_ORIGINS` setting (comma-separated env var, defaults to `http://localhost:5173` and `http://127.0.0.1:5173` — distinct origins for the browser), so new origins are added by configuration, not code. All methods and headers are allowed — this covers the `Authorization` bearer header and the login request. This is **dev-origin CORS only**; production hardening (locked-down origins, credentials policy) is out of scope.

| Variable | Description |
|---|---|
| `CORS_ALLOW_ORIGINS` | Comma-separated list of allowed origins. Default `http://localhost:5173` |

#### users/ slice

`User` stores credentials and role for every person who can call the API. Roles: `admin`, `staff`, `member`.

`UserRole` is a `StrEnum`. When read back from PostgreSQL, the value is a plain `str` — comparing with `UserRole.member` (not `.value`) works because `StrEnum.__eq__` compares by value.

#### members/ slice

`Member` no longer holds an email column. Email is owned by the linked `User` (via `member.user_id` FK). Operations that need email (list, get, update) return `tuple[Member, str]` from the repository. `LoanService` calls `get_by_id` (no email needed) to avoid the join overhead.

`POST /members` provisions a linked `member`-role `User`, sets a random initial password, and returns it once in `MemberCreateResponse.initial_password`. Subsequent reads omit it.

`DELETE /members/{id}` returns `409` when the member still has loans: the `loans.member_id` FK is `ON DELETE RESTRICT`, so `SqlModelMemberRepository.delete` catches the `IntegrityError`, recognises `MEMBER_FK_CONSTRAINT` (defined in `app/loans/domain/loan_model.py`) via `is_constraint_violated`, and raises `MemberHasLoansError`, which the router maps to `409`. This mirrors the `BookHasCopiesError` pattern.

### Testing

`tests/conftest.py` provides two HTTP client fixtures:

| Fixture | Auth behaviour |
|---|---|
| `client` | Overrides `get_current_user` with a fake staff user — use for all non-auth feature tests |
| `auth_client` | No override — use for testing real login / token validation flows |

- The `db_setup` fixture runs Alembic migrations before each test (`upgrade head`) and rolls them back after (`downgrade base`). No explicit migration step is needed in CI.
- Coverage target: aim for close to 100%. Use `# pragma: no cover` only for genuinely untestable lines — abstract method stubs and dependency-injection wiring replaced in tests.

## Frontend

A self-contained browser SPA lives under `/frontend` (Option A: the backend stays at the repo root, untouched). It exists to visualize and exercise the API. Authentication is in place (log in, hold a JWT) behind a routed, authenticated layout; entity views are being built out incrementally per the `frontend-api-parity` OpenSpec change (full Books CRUD and Members management done; copies, loans pending).

### Stack

| Layer | Choice |
|---|---|
| Language | TypeScript |
| Framework | React 19 |
| Routing | React Router (`react-router`) |
| Server state | TanStack Query (`@tanstack/react-query`) |
| Build / dev server | Vite (HMR) |
| Styling | Tailwind CSS (via the `@tailwindcss/vite` plugin) |
| Package manager | pnpm |
| Linting & formatting | ESLint + Prettier |
| Testing | Vitest + React Testing Library (jsdom) |

### Layout

Under `frontend/src/`: `api/` (apiClient wrapper, hand-written types, typed call functions, `errors.ts` form-message helper), `auth/` (tokenStore storage seam, AuthContext/AuthProvider, `useCurrentUser` query, `roles.ts` gating helpers), `components/` (screens + `ProtectedLayout`), `queryClient.ts` (the single `QueryClient`), `routes.ts` (shared route constants), and `App.tsx` defining the route tree.

**Routing & layout.** `App.tsx` is a React Router route tree, not a boolean toggle: a `/login` route plus a `ProtectedLayout` (nav + sign-out + `<Outlet/>`) wrapping the resource routes (`/books`, `/books/new`, `/books/:id/edit`, …). `ProtectedLayout` redirects unauthenticated access to `/login`; `LoginScreen` navigates to the default authenticated route (`/books`) on success and redirects there if already authenticated. Provider order (`main.tsx`): `QueryClientProvider` → `BrowserRouter` → `AuthProvider`.

**Server state.** All reads/writes go through TanStack Query over the existing `apiClient` seam — `useQuery` with per-resource keys (e.g. `["books"]`, `["book", id]`, `["currentUser"]`); mutations (`useMutation`, e.g. the Books create/edit/delete forms) call `apiClient` and `invalidateQueries` the affected keys so lists/details refresh. Sign-out calls `queryClient.clear()` so one session's cached data never leaks into the next.

**Role-aware UI.** `useCurrentUser` (`GET /auth/me`) exposes the role; `src/auth/roles.ts` centralizes the role→action gating (e.g. `canManageBooks` → `admin`/`staff` see create/edit/delete; `member` is read-only). For members, `canManageMembers` (`admin`/`staff`) gates create/edit, while `canDeleteMembers` (`admin` only) gates the destructive delete — the matrix is pinned per entity slice, so it can diverge between entities. This is **UX-only** — the backend does not enforce role authorization, so it merely hides controls; it is not a security boundary.

All backend calls go through a single `apiClient` helper (`src/api/client.ts`): it prepends `VITE_API_BASE_URL`, attaches `Authorization: Bearer <token>` when a token is stored, parses JSON, and throws `ApiError` on non-success. `apiErrorToFormMessage` (`src/api/errors.ts`) maps a thrown `ApiError` to a form-level message (surfacing backend `detail` for `409`/`422`), falling back to a generic message for non-`ApiError` throws. Types are hand-written (`src/api/types.ts`); generating from OpenAPI is deferred.

**Form validation.** Forms validate client-side before submitting, mirroring the backend's rules so invalid input never costs a `422` round-trip (`409` conflicts like a duplicate ISBN are not knowable client-side and still surface from the server). Validation lives next to its form in a testable module — e.g. `src/components/bookValidation.ts` ports the backend ISBN-10/13 checksum check from `app/books/domain/book_model.py` and enforces required/length/whole-number-year rules, returning a per-field error map the form renders inline. Keep these in sync when the backend rules change.

The token lives behind `src/auth/tokenStore.ts` so the storage mechanism can be hardened without touching call sites. The frontend calls the API **directly cross-origin** (no Vite proxy), relying on backend CORS (see the CORS section).

### Commands

Run pnpm scripts from `/frontend` (`pnpm install`, `dev`, `build`, `typecheck`, `lint`, `format` — see `package.json`). `pnpm install` once first; `dev` is also reachable from the repo root via `make dev-frontend`. Configuration (`VITE_API_BASE_URL`, default `:8077` to match the backend) lives in `.env.example`.

### Dependencies

The Node toolchain is fully isolated under `/frontend` — independent of the Python `pyproject.toml`. `pnpm-lock.yaml` is committed (the analog of `uv.lock`); `frontend/node_modules`, `frontend/dist`, and `frontend/coverage` are gitignored.

Pinning policy (the frontend analog of the backend's; keep the two aligned):

- All direct dependencies in `package.json` use exact version pins (`"package": "X.Y.Z"`, no `^`/`~`), both runtime and dev
- `pnpm-lock.yaml` is committed; it pins transitive dependencies and integrity hashes
- Upgrades are deliberate: `pnpm add package@X.Y.Z` or edit `package.json` and run `pnpm install`
- Every PR that modifies `package.json` or `pnpm-lock.yaml` must have its dependency diff reviewed explicitly before merge
- In automated environments (CI, prod, once they exist), use `pnpm install --frozen-lockfile` so resolution is forbidden

### Testing

Frontend tests use **Vitest + React Testing Library** in a `jsdom` environment. Test files sit next to the code they cover (`*.test.ts` / `*.test.tsx`); shared helpers live in `src/test/` (`setup.ts` wires jest-dom matchers and per-test cleanup; `utils.tsx` provides `renderWithAuth`, a `jsonResponse` builder, and a `makeBook` factory). `renderWithAuth` wraps the UI in the app's providers — a fresh per-render `QueryClient` (retries off), a `MemoryRouter` (override the history stack via `{ initialEntries }`), and the real `AuthProvider`. Vitest globals are **off** — import `describe`/`it`/`expect`/`vi` explicitly.

Tests exercise behaviour through the public seams: `fetch` is stubbed with `vi.stubGlobal` (no MSW yet) and assertions go through the real `apiClient`, `tokenStore`, and `AuthProvider` rather than mocking them. Coverage is **reported, not gated** — the seams and logic (`apiClient`, `tokenStore`) should stay near 100%, while UI components are best-effort; there is no failing threshold, so don't chase defensive branches.

## AI Collaboration Rules

**Debate before executing.** If something seems wrong, missing, inconsistent, or improvable, raise it and discuss options before proceeding. Do not execute blindly.

**Keep this file up to date.** If during development a decision is made, a convention is added, or anything worth documenting changes, update `CLAUDE.md` accordingly in the same PR where the change happens.
