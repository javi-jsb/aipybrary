## 1. Harness & tooling (sub-issue 1)

- [ ] 1.1 Add `@playwright/test` to `/frontend` as an exact-pinned dev dependency; commit `pnpm-lock.yaml` (dependency diff reviewed per policy)
- [ ] 1.2 Install Chromium via `playwright install chromium` and document the one-time step
- [ ] 1.3 Add `playwright.config.ts` with Chromium-only project, traces/screenshots on failure, and base URL pointing at the Vite-served SPA
- [ ] 1.4 Configure Playwright `webServer` to boot Postgres, the FastAPI server on `:8077`, and the Vite SPA for a run (reusing an already-running server locally where possible)
- [ ] 1.5 Add a `test:e2e` script to `frontend/package.json` that runs the suite headless; optionally expose a `make` target
- [ ] 1.6 Create the `e2e/` test directory and add a smoke spec that loads the app and asserts the login screen renders

## 2. Test data & isolation (sub-issue 2)

- [ ] 2.1 Provision a dedicated `aipybrary_e2e` logical database on the same Postgres engine, schema-migrated via the existing Alembic migrations
- [ ] 2.2 Point the `webServer`-started API process at the E2E database via environment configuration; fail fast if the target DB is not the dedicated E2E one
- [ ] 2.3 Implement a deterministic seed for E2E (reusing the existing `database-seeding` capability where possible)
- [ ] 2.4 Implement a truncate + re-seed reset between specs/workers so specs are order-independent; tune granularity based on observed runtime
- [ ] 2.5 Implement a reusable login/JWT fixture with role-scoped sessions for `admin`, `staff`, and `member`

## 3. Flows per area (sub-issue 3)

- [ ] 3.1 Auth: successful login navigates to the authenticated app; invalid credentials surface an error
- [ ] 3.2 Books CRUD: create, edit, and delete a book; assert each reflected in list/detail views
- [ ] 3.3 Members: create a member and assert the one-time initial password is shown once and absent on subsequent reads; cover edit
- [ ] 3.4 Book copies: add and remove copies; assert the copies view reflects changes
- [ ] 3.5 Loans: borrow and return a copy; assert success and that a business-rule violation surfaces its error
- [ ] 3.6 Role-aware visibility: assert role-gated controls are shown/hidden per role across the covered areas

## 4. Wrap-up

- [ ] 4.1 Update CLAUDE.md (Frontend → Testing) to describe the E2E layer, the `test:e2e` entry point, and the dedicated E2E database
- [ ] 4.2 Open the per-area sub-issues under umbrella #93 mapping to task groups 1–3
- [ ] 4.3 Verify the full suite runs green locally end-to-end (Chromium, headless)
