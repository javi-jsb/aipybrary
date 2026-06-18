# e2e-testing Specification

## Purpose
TBD - created by archiving change e2e-playwright-tests. Update Purpose after archive.
## Requirements
### Requirement: End-to-end tests exercise the real application stack

The system SHALL provide end-to-end tests that drive the real SPA in a real browser against the real API and database (browser → frontend → FastAPI → Postgres), rather than stubbing the HTTP transport. Tests SHALL be authored with Playwright (`@playwright/test`), pinned to an exact version with the lockfile committed.

#### Scenario: A flow runs against the real stack

- **WHEN** an end-to-end test performs a user action in the browser
- **THEN** the action SHALL reach the running FastAPI server over HTTP and persist to the database, with no stubbed `fetch` or mocked API transport

#### Scenario: Playwright dependency is pinned

- **WHEN** the E2E tooling is added to the frontend
- **THEN** `@playwright/test` SHALL be declared with an exact version in `package.json` and `pnpm-lock.yaml` SHALL be committed

### Requirement: The E2E run orchestrates the full stack locally

The system SHALL provide a single local entry point (a `pnpm` script, e.g. `test:e2e`) that boots the full stack via Playwright's `webServer` orchestration — Postgres, the FastAPI server on port `8077`, and the Vite-served SPA — and runs the suite headless. The E2E suite SHALL NOT be wired into any CI pipeline as part of this initiative.

#### Scenario: One command runs the suite

- **WHEN** a developer runs the E2E entry point locally
- **THEN** Playwright SHALL ensure Postgres, the API on `:8077`, and the SPA are available, then execute the suite headless and report results

#### Scenario: No CI integration

- **WHEN** this initiative is implemented
- **THEN** no CI workflow SHALL be added or modified to run the E2E suite

### Requirement: E2E tests use a dedicated, isolated database

The system SHALL run end-to-end tests against a dedicated logical database on the same Postgres engine (distinct from the developer's dev and backend-test databases), provisioned with the existing Alembic migrations. The harness SHALL NOT depend on pytest's in-process migration fixtures for isolation.

#### Scenario: Dedicated database is provisioned via migrations

- **WHEN** the E2E suite starts
- **THEN** the API process SHALL be pointed at the dedicated E2E database, which SHALL be schema-migrated using the existing Alembic migrations

#### Scenario: Specs are isolated from one another

- **WHEN** the suite runs multiple specs
- **THEN** each spec SHALL start from a known, deterministic data state via truncate and re-seed, so specs are order-independent and do not leak data between one another

#### Scenario: Dev and test data are never touched

- **WHEN** the E2E suite runs
- **THEN** it SHALL operate only on the dedicated E2E database and SHALL NOT modify the developer's dev database or the backend pytest database

### Requirement: A reusable authentication fixture provides role-scoped sessions

The system SHALL provide a reusable Playwright fixture that authenticates against the real login endpoint, holds the resulting JWT/session, and reuses it across specs. The fixture SHALL support distinct sessions for the `admin`, `staff`, and `member` roles so that role-aware behavior can be exercised.

#### Scenario: Authenticated session is reused

- **WHEN** a spec requires an authenticated user of a given role
- **THEN** the fixture SHALL provide a logged-in session for that role without each test repeating the full login UI flow

### Requirement: E2E coverage spans all application areas

The end-to-end suite SHALL cover the application's user-facing flows: authentication (login and JWT handling), books CRUD, members management (including surfacing the one-time initial password on creation), book-copy management, loans (borrow and return, including business-rule error paths), and role-aware UI visibility.

#### Scenario: Authentication flow

- **WHEN** a user logs in with valid credentials and later with invalid credentials
- **THEN** the suite SHALL assert successful authenticated navigation in the first case and a surfaced error in the second

#### Scenario: Books CRUD flow

- **WHEN** an authorized user creates, edits, and deletes a book through the SPA
- **THEN** the suite SHALL assert each operation is reflected in the list/detail views

#### Scenario: Members creation surfaces the initial password

- **WHEN** an authorized user creates a member
- **THEN** the suite SHALL assert the one-time initial password is shown once on creation and not on subsequent reads

#### Scenario: Book-copy management flow

- **WHEN** an authorized user adds and removes copies of a book
- **THEN** the suite SHALL assert the copies view reflects the changes

#### Scenario: Loans borrow and return, including error paths

- **WHEN** an authorized user borrows and returns a copy, and attempts an operation that violates a business rule
- **THEN** the suite SHALL assert the successful borrow/return and that the business-rule error is surfaced

#### Scenario: Role-aware visibility

- **WHEN** users of different roles view the application
- **THEN** the suite SHALL assert that role-gated controls are visible or hidden according to the role's permissions

