## Context

The project has no CI pipeline. Tests require a live PostgreSQL database, which locally runs via Docker Compose. The app configuration (`app/config.py`) reads individual `POSTGRES_*` environment variables through pydantic-settings and builds the connection URL as a computed field — there is no single `DATABASE_URL` env var. The `tests/conftest.py` fixture runs Alembic migrations automatically (`upgrade head` / `downgrade base`) around each test, so no explicit migration step is needed in CI.

## Goals / Non-Goals

**Goals:**
- Run `make check` (lint) and `make coverage` (tests + implicit migrations) on every push and PR targeting `main`
- Extract coverage percentage and update a Gist-backed badge via shields.io
- Display a workflow status badge in `README.md`

**Non-Goals:**
- Deployment or staging environments
- Matrix testing across Python versions or Postgres versions
- Performance or load testing
- Caching strategies (added only if build times justify it)

## Decisions

### 1. GitHub Actions service containers over Docker Compose in CI
Service containers are a first-class GHA primitive: they start before job steps, expose the port on `localhost`, and support health checks. No `docker compose up` step, no waiting loops, no extra tooling.

*Alternative considered*: run `make db-up` in a step. Rejected — adds latency and complexity for no benefit.

### 2. Individual `POSTGRES_*` env vars, not a single `DATABASE_URL`
The app already uses individual vars; injecting them as-is requires zero changes to application or test code.

*Alternative considered*: add a `DATABASE_URL` env var and refactor `config.py`. Rejected — out of scope; adds risk for no gain.

### 3. Single database: `POSTGRES_DB=aipybrary_test`
The service container creates whichever DB is named in `POSTGRES_DB`. Setting both `POSTGRES_DB` and `POSTGRES_TEST_DB` to `aipybrary_test` means the container creates the test DB directly — no init script needed. The app's `database_url` (non-test) is never exercised in the test suite.

### 4. Gist + `Schneegans/dynamic-badges-action` for coverage badge
CI extracts the coverage percentage with `uv run coverage report --format=total` and writes a JSON file to a secret Gist via a PAT scoped to `gist` only. shields.io reads the Gist endpoint and renders the badge. No third-party service receives repo access or OAuth permissions.

*Alternative considered*: Codecov — rejected because its OAuth flow requests "act on your behalf" (can comment PRs, read repo), which is more access than needed for a badge.

*Alternative considered*: `genbadge` committing an SVG to the repo — rejected because it generates a commit on every CI run (noisy history) and requires GitHub Pages or a static host for the badge URL.

### 5. Badge update runs only on push to `main`, not on PRs
The `Update coverage badge` step is gated with `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`. PRs run the full test and coverage steps but do not overwrite the badge, so the README always reflects the state of `main`.

### 6. `make coverage` in CI instead of `make test`
`make coverage` runs the full test suite and also writes coverage data to disk, which the subsequent extraction step reads. There is no need for a separate `make test` step.

## Risks / Trade-offs

- **Gist PAT expiry** → If the `gist`-scoped PAT expires, the badge stops updating (CI still passes). Mitigation: set a calendar reminder to rotate the PAT, or use a non-expiring token.
- **postgres:17 image download time** → First run pulls ~75 MB. Acceptable; GHA caches layer pulls across runs.

## Migration Plan

1. Add `.github/workflows/ci.yml` — no existing workflow to migrate.
2. Add badge links to `README.md` — purely additive.
3. Create a secret Gist, generate a `gist`-scoped PAT, and store it as `GIST_TOKEN` in GitHub Actions repository secrets.

No rollback needed — deleting the workflow file reverts CI; removing badge lines reverts the README.
