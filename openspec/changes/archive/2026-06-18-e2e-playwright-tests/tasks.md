## 1. Harness & tooling (sub-issue 1)

- [x] 1.1 Add `@playwright/test` to `/frontend` as an exact-pinned dev dependency; commit `pnpm-lock.yaml` (dependency diff reviewed per policy)
- [x] 1.2 Install Chromium via `playwright install chromium` and document the one-time step
- [x] 1.3 Add `playwright.config.ts` with Chromium-only project, traces/screenshots on failure, and base URL pointing at the Vite-served SPA
- [x] 1.4 Configure Playwright `webServer` to boot the Vite SPA (reusing an already-running server locally where possible). NOTE: booting Postgres + FastAPI on `:8077` is inseparable from the dedicated E2E database and moves to the data/isolation slice (group 2 / #97)
- [x] 1.5 Add a `test:e2e` script to `frontend/package.json` that runs the suite headless; optionally expose a `make` target
- [x] 1.6 Create the `e2e/` test directory and add a smoke spec that loads the app and asserts the login screen renders

## 2. Test data & isolation (sub-issue 2)

- [x] 2.1 Provision a dedicated `aipybrary_e2e` logical database on the same Postgres engine, schema-migrated via the existing Alembic migrations (`scripts/e2e_db.py provision`, `make db-e2e-provision`, Playwright `globalSetup`)
- [x] 2.2 Point the `webServer`-started API process at the E2E database via environment configuration (`make e2e-api` sets `POSTGRES_DB`); fail fast if the target DB is not the dedicated E2E one (guard in `scripts/e2e_db.py`)
- [x] 2.3 Implement a deterministic seed for E2E (single shared password hash; reuses the same domain models as `scripts/seed.py`)
- [x] 2.4 Implement a truncate + re-seed reset between specs (auto `resetDb` fixture in `e2e/fixtures.ts` → `make db-e2e-reset`)
- [x] 2.5 Implement a reusable login/JWT fixture with role-scoped sessions for `admin`, `staff`, and `member` (`loginAs` in `e2e/fixtures.ts`)

## 3. Flows per area (sub-issue 3)

- [x] 3.1 Auth: successful login navigates to the authenticated app; invalid credentials surface an error (`e2e/auth.spec.ts`)
- [x] 3.2 Books CRUD: create, edit, and delete a book; assert each reflected in the list (`e2e/books.spec.ts`)
- [x] 3.3 Members: create a member and assert the one-time initial password is shown once and absent on a subsequent read (`e2e/members.spec.ts`)
- [x] 3.4 Book copies: add and remove a copy; assert the copies view reflects changes (`e2e/copies.spec.ts`)
- [x] 3.5 Loans: borrow and return a copy; assert success and that a business-rule violation (active-loan limit) surfaces its error (`e2e/loans.spec.ts`)
- [x] 3.6 Role-aware visibility: assert role-gated controls are shown for admin and hidden for member across the covered areas (`e2e/roles.spec.ts`)

## 4. Wrap-up

- [x] 4.1 Update CLAUDE.md (Frontend → Testing) to describe the E2E layer, the `test:e2e` entry point, and the dedicated E2E database
- [x] 4.2 Open the per-area sub-issues under umbrella #93 mapping to task groups 1–3 (#96, #97, #98)
- [x] 4.3 Verify the full suite runs green locally end-to-end (Chromium, headless) — 15 passed
