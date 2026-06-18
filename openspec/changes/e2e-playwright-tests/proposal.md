## Why

Automated coverage stops at the seams: backend `pytest` integration tests hit a real DB but never touch the SPA, and frontend Vitest tests stub `fetch` so they never reach the real API. Nothing exercises the real browser → real frontend → real FastAPI → real Postgres path, so frontend↔backend parity (umbrella #64) is only verified by a one-off manual pass. This change establishes true end-to-end coverage for the whole application.

Scope of **this** change is deliberately narrow: produce the OpenSpec artifacts (proposal, spec deltas, tasks) that define the E2E initiative and from which per-area sub-issues are derived. **No E2E code is written here** — implementation lands in the sub-issues.

## What Changes

- Introduce an **`e2e-testing`** capability that specifies how the application is tested end-to-end: tooling, stack orchestration, data isolation, and which user flows must be covered.
- **Tooling: Playwright** (TS-native, auto-wait, multi-browser, `webServer` orchestration), pinned per the repo's exact-version policy, with its lockfile committed.
- **Real-stack execution**: tests drive the deployed SPA against the real API (browser → frontend → FastAPI on `:8077` → Postgres), not stubbed-transport component tests.
- **Dedicated logical E2E database** on the same Postgres engine (e.g. `aipybrary_e2e`), provisioned with the existing Alembic migrations, with truncate/re-seed isolation between specs orchestrated by Playwright — not pytest's in-process upgrade/downgrade fixtures (the API server runs as a separate process under `webServer`).
- **Local-execution only**: a `pnpm`-driven entry point that boots the stack via Playwright's `webServer`. **No CI integration** in this initiative (possible future follow-up).
- **Browser matrix: Chromium-only** to start.
- **Flow coverage** specified across: auth/login + JWT, books CRUD, members (incl. one-time initial password), book copies, loans (borrow/return + business-rule errors), and role-aware visibility.

## Capabilities

### New Capabilities
- `e2e-testing`: End-to-end test coverage of the whole application — Playwright tooling and pinning, real-stack `webServer` orchestration (Postgres + FastAPI + Vite), dedicated E2E database with between-spec isolation, a reusable login/JWT fixture, local-only execution, and the catalogue of user flows that must be covered.

### Modified Capabilities
<!-- None. This change only adds testing infrastructure; it does not alter the requirements of any existing capability. -->

## Impact

- **Frontend** (`/frontend`): new dev dependency `@playwright/test` (pinned), Playwright config with `webServer` orchestration, a `test:e2e` script in `package.json`, and an `e2e/` test directory. `pnpm-lock.yaml` updated (dependency diff reviewed per policy).
- **Backend / data**: a dedicated `aipybrary_e2e` database provisioned via existing Alembic migrations; truncate/re-seed strategy reusing the existing `database-seeding` capability where possible. No backend source changes expected beyond test-data/seed orchestration wiring.
- **Local dev workflow**: documented `pnpm test:e2e` entry point that boots the full stack; `make` target optional. CLAUDE.md (Frontend → Testing) updated to describe the E2E layer.
- **Process**: per-area sub-issues opened under umbrella #93 from the tasks defined here. No CI/pipeline changes.
