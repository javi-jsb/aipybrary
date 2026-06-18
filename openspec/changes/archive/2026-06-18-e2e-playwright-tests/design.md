## Context

The app has full frontend↔backend parity (#64) but no end-to-end safety net. Backend `pytest` tests hit a real Postgres but never render the SPA; frontend Vitest tests stub `fetch` and never reach the API. The only whole-stack verification to date was a manual pass (task 7.1 of `frontend-api-parity`).

Constraints that shape the approach:
- The frontend is a self-contained React 19 + Vite SPA under `/frontend` with its own pnpm toolchain; the backend is FastAPI + SQLModel at the repo root, served on `:8077` (`make dev`).
- Backend test isolation today lives in pytest's `db_setup` fixture (`alembic upgrade head` / `downgrade base` per test) — **in-process**. E2E cannot reuse it because the API runs as a separate OS process under Playwright's `webServer`.
- The repo follows an incremental, spec-driven ethos: one slice (sub-issue) at a time, exact-version pinning, lockfiles committed, English-only public content.

This change produces only the OpenSpec artifacts; implementation happens in the sub-issues derived from `tasks.md`.

## Goals / Non-Goals

**Goals:**
- Define the E2E architecture: tooling (Playwright), real-stack orchestration, data isolation, and the catalogue of flows to cover.
- Make the design directly translatable into the per-area sub-issues under umbrella #93.
- Keep the data strategy deterministic and independent of pytest's fixtures.

**Non-Goals:**
- Writing any E2E test code, Playwright config, or seed scripts (those land in the sub-issues).
- CI/pipeline integration — explicitly out of scope for this initiative (local execution only).
- Multi-browser coverage — Chromium-only to start.
- Changing any existing backend or frontend behavior; this adds a testing layer only.

## Decisions

### D1 — Tooling: Playwright (`@playwright/test`)
TS-native (matches the frontend stack), auto-waiting (less flaky than manual waits), first-class `webServer` orchestration, and traces/screenshots on failure. Pinned to an exact version; `pnpm-lock.yaml` committed.
- *Alternatives:* Cypress (heavier, weaker multi-tab/process story, non-TS-first config); Selenium/WebdriverIO (more boilerplate, slower iteration). Rejected for ergonomics and stack fit.

### D2 — Real-stack execution via `webServer`
Playwright's `webServer` boots the full stack for a run: Postgres (Docker), FastAPI on `:8077`, and the Vite-served SPA. Tests drive a real Chromium browser against the running SPA, which calls the real API cross-origin (existing CORS config already allows the Vite origin). This validates the exact browser → frontend → API → DB path, including auth headers and CORS.
- *Alternative:* component tests with a stubbed transport (what Vitest already does) — rejected, it is precisely the gap this change closes.

### D3 — Dedicated logical E2E database, provisioned by Alembic
A separate logical database on the **same Postgres engine** (e.g. `aipybrary_e2e`), created and schema-migrated with the existing Alembic migrations (`upgrade head`). The API process started by `webServer` is pointed at it via environment configuration (database URL), so E2E never touches the developer's dev/test data.
- *Alternative:* reuse the backend's pytest test DB lifecycle — rejected: that lifecycle is in-process to pytest and cannot be shared with a separate server process.

### D4 — Between-spec isolation: truncate + re-seed, orchestrated by Playwright
Each spec (or worker) starts from a known state. A reset step truncates the data tables and re-applies a deterministic seed (reusing the existing `database-seeding` capability where possible) between specs. This keeps tests order-independent without per-test migration churn.
- *Alternative A:* transactional rollback per test — rejected, impractical across an out-of-process HTTP server. *Alternative B:* per-spec fixtures that create/clean their own data via the API — viable but more verbose; truncate+seed is the baseline, with API-driven setup layered on top where a spec needs specific data.

### D5 — Reusable login/JWT fixture
A Playwright fixture performs the login flow once and reuses the authenticated session (storage state / token) across specs that need a given role, avoiding a login round-trip per test. Distinct fixtures cover the `admin`/`staff`/`member` roles to exercise role-aware visibility.

### D6 — Local execution only, Chromium-only
A `pnpm test:e2e` script runs the suite headless locally via `webServer`. No GitHub Actions wiring in this initiative. Chromium is the only browser in the matrix initially; the config is structured so more browsers can be added later without restructuring.

## Risks / Trade-offs

- **Flakiness from real-stack timing** → Rely on Playwright auto-wait and explicit state assertions; enable traces/screenshots on failure for diagnosis. Avoid fixed `sleep`s.
- **Slow startup (Docker + API + Vite) per run** → `webServer` reuses an already-running server locally where possible; the suite is local/on-demand, not in CI, so wall-clock cost is acceptable.
- **Truncate/re-seed coupling to schema** → Reuse the existing seed and migration tooling rather than hand-maintained SQL, so schema changes flow through one place.
- **Accidental pointing at dev/test DB** → The E2E database name and URL are explicit and distinct; the harness fails fast if the target DB is not the dedicated E2E one.
- **Scope creep into CI** → Kept explicitly out of scope; revisit as a separate follow-up issue.

## Open Questions

- Exact reset granularity (per-spec vs per-worker vs per-file) — to be tuned in the test-data/isolation sub-issue based on observed runtime.
- Whether the dedicated E2E DB is provisioned by a `make`/`pnpm` script or by Playwright `globalSetup` — to be decided in the harness sub-issue.
- How much to assert on backend state (via API) vs UI-only assertions per flow — defaulting to UI-first, with API assertions where a UI signal is insufficient.
