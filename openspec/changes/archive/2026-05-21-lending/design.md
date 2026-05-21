## Context

`aipybrary` now has a `Member` entity (Phase 1) and `BookCopy` physical copies (Phase 2). What it lacks is the ability to connect them: a member borrowing a copy and returning it. This change introduces the `Loan` entity, the `loans/` vertical slice, and the business rules that govern the borrow/return lifecycle.

This is the first service in the project that orchestrates three repositories simultaneously (`LoanRepository`, `MemberRepository`, `BookCopyRepository`), making it the clearest demonstration of the hexagonal architecture's value: invariants live in the application layer, repositories are pure persistence abstractions.

The `loan` domain also introduces the first action-based endpoints (sub-resources) in the project, and the first derived computed field at the schema level (`LoanStatus`).

## Goals / Non-Goals

**Goals:**

- A `loans/` slice structurally identical to `members/` and `book_copies/` (`domain/` / `application/` / `infrastructure/`).
- A `Loan` entity with three timestamps (`created_at`, `updated_at`, `returned_at`) covering the full lifecycle.
- Derived `LoanStatus` (`active` / `overdue` / `returned`) as a `@computed_field` — no stored status column, no cron job.
- Five endpoints: list, get-by-id, borrow, return, undo-return, cancel.
- Business invariants enforced in `LoanService`: suspended member blocked, copy not double-lent, per-member loan limit.
- Configurable loan policy (`loan_period_days`, `loan_max_active`) via `config.py` env vars.
- `copies_available` field in `BookPublic` (deferred from Phase 2), computed without N+1.
- `seed.py` gains `SAMPLE_BOOK_COPIES` (missing from Phase 2) and `SAMPLE_LOANS` (all three status states).
- Reversible Alembic migration.

**Non-Goals:**

- Reservations / FIFO queue for unavailable copies (Phase 4).
- Loan renewals or extensions.
- Editing the return timestamp to a specific date (admin correction is limited to undoing the return via `DELETE /loans/{id}/return`).
- `Member` or `BookCopy` deletion when loan history exists (FK `RESTRICT` enforces this at the DB level).
- Shared/refactored cross-slice primitives (tracked in #25, still deferred).

## Decisions

**Three timestamps: `created_at`, `updated_at`, `returned_at`.**
`Loan` has three temporal fields, not two. `created_at` is semantically the "borrowed at" timestamp — the loan's creation IS the borrow event — and using `created_at` is consistent with all other entities in the codebase. `returned_at` is the explicit domain event of returning (nullable; null = active or overdue). `updated_at` is the infrastructure audit field: it changes whenever the record is modified, which matters because `DELETE /loans/{id}/return` (undo return) sets `returned_at` back to null — `updated_at` captures when that correction happened. Alternative considered: `borrowed_at` instead of `created_at` — rejected for inconsistency with other entities, where `created_at` is always the creation timestamp. Alternative: drop `updated_at` (only two timestamps) — rejected because there would be no audit trail for admin corrections.

**`LoanStatus` derived at read time, not stored.**
`LoanPublic` exposes a `status: LoanStatus` computed field (`@computed_field`) derived from `returned_at` and `due_date`. No `status` column in the DB. Alternative: store status as an enum column — rejected because transitioning ACTIVE→OVERDUE requires a cron job (or stale data), adding operational complexity with no benefit since the derivation is a two-field comparison. Alternative: no `status` in the API response — rejected because clients should not need to re-derive it on every response.

**Action endpoints for return and undo-return; no general PATCH.**
`POST /loans/{id}/return` marks a loan returned. `DELETE /loans/{id}/return` undoes a mistaken return. No `PATCH /loans/{id}` with arbitrary fields. Alternative: `PATCH /loans/{id}` with `{ "returned_at": null }` — rejected because a PATCH body that only ever accepts one value is semantically an action, not an update. Removing the body altogether and using a dedicated endpoint is clearer and harder to misuse. The symmetric pair `POST ... /return` ↔ `DELETE ... /return` matches the existing pattern of explicit action endpoints and is self-documenting. Alternative: allow `PATCH` with any `returned_at` datetime — rejected because changing the return timestamp to an arbitrary value (e.g., backdating) is not a supported use case and would require additional validation without adding clear value for this phase.

**`DELETE /loans/{id}` only for active/overdue loans.**
A returned loan is an audit record — immutable. An active loan that was created by mistake can be cancelled (removed entirely). The service invariant: `returned_at IS NOT NULL` → 409. Alternative: no DELETE at all — rejected because there is no other way to correct "created by mistake" without polluting the return history. Alternative: DELETE for all loans — rejected because it destroys completed-transaction history.

**`LoanService` orchestrates three repositories via constructor injection.**
`LoanService.__init__` receives `LoanRepository`, `MemberRepository`, and `BookCopyRepository` as ABCs. Invariant checks call these repos in sequence before persisting. The router wires up the concrete SQLModel implementations. This mirrors `BookCopyService` (which already injects two repos) and is the established pattern — the router's `_get_service` factory function is the only place concrete implementations are referenced. The service never imports SQLModel.

**`copies_available` in `BookPublic` via correlated subquery, importing `Loan` in books infrastructure.**
The `sql_book_repository.py` (infrastructure layer) computes `copies_available` as a correlated scalar subquery using `col(Loan.book_copy_id)` and `col(Loan.returned_at)` directly. The `Loan` SQLModel class is imported from `app.loans.domain.loan_model`. This is an infrastructure-to-infrastructure cross-slice dependency, which is acceptable — the rule that matters is that domain layers do not import from other slices; infrastructure layers may. The dependency is unidirectional (`books` → `loans`) with no risk of circular imports. Referencing `Loan` columns by name rather than by model was considered but rejected: it provides no real decoupling (the table and column names are still hardcoded), while losing static type checking and refactoring support. Alternative: compute in `BookService` with a separate query — rejected (N+1).

**FK constraints: `ON DELETE RESTRICT` for both FKs on `loans`.**
`loans.member_id → members.id` and `loans.book_copy_id → book_copies.id` are both `ON DELETE RESTRICT`. A member or book copy with any loan history (even returned loans) cannot be deleted. This preserves the audit trail. The trade-off (harder to clean up test data, harder to delete members) is accepted: this is an intentional design choice that forces explicit resolution before deletion.

**Settings for loan policy in `config.py`.**
`loan_period_days: int` (default 14) and `loan_max_active: int` (default 3) are added to the existing Pydantic Settings class. They can be overridden via environment variable with no code change. Alternative: hard-coded in the service — rejected because loan policies vary by library and requiring a redeploy to change them is unnecessary. Alternative: `LoanPolicy` database table — rejected as overkill for a single-library system.

**Seeding order: books → members → book_copies → loans.**
The `seed.py` script gains two new idempotent blocks: `SAMPLE_BOOK_COPIES` (missing from Phase 2) and `SAMPLE_LOANS`. Each block checks independently for the presence of existing records before inserting. Loans are the last block because they require the IDs of already-seeded members and book copies. The loan seed dataset covers all three states (active, overdue, returned) to make the list endpoint's status filter exercisable manually.

**`due_date` set by the service at borrow time; not client-supplied.**
`LoanCreate` only carries `member_id` and `book_copy_id`. The service computes `due_date = now() + timedelta(days=settings.loan_period_days)`. Alternative: let the client supply `due_date` — rejected because loan duration is a library policy, not a client decision.

## Risks / Trade-offs

- **Loan history blocks member/copy deletion** → Accepted. This is correct behaviour for a library system; cleaning up test data requires either resetting the DB or returning all active loans first.
- **No backdating returns** → If a librarian needs to record that a book was returned yesterday, there is no supported path in this phase. The trade-off (simpler API surface) is accepted; a future admin-correction capability could address this.
- **`OVERDUE` status has second-level precision** → A loan flips from `active` to `overdue` at the exact `due_date` UTC timestamp. There is no grace period. This is intentional and simple; a grace-period requirement would be an explicit future addition.
- **Seeding loans requires querying member and book_copy IDs** → The loan seed block must look up seeded members and book copies by email/barcode. This couples seed data but is acceptable for a dev-only script.

## Migration Plan

1. Add `loan_period_days` and `loan_max_active` to `config.py`.
2. Create the `loans/` slice (domain → application → infrastructure).
3. Register the router in `src/app/main.py`.
4. Add the `copies_available` subquery to `sql_book_repository.py` and `BookPublic`.
5. Author the Alembic migration: `CREATE TABLE loans (...)` with both FK constraints. Verify `upgrade head` then `downgrade -1` round-trips cleanly.
6. Update `scripts/seed.py` with `SAMPLE_BOOK_COPIES` and `SAMPLE_LOANS` blocks.
7. Ship under `feat/23-lending` referencing `Closes #23`; archive separately per OpenSpec convention.

Rollback: `alembic downgrade -1` drops the `loans` table; the slice code is removed with the PR revert. `copies_available` removal from `BookPublic` requires a matching PR. No data migration (new table, no dependents in Phase 3).

## Open Questions

None — all decisions resolved during exploration.
