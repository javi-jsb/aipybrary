## Why

`aipybrary` has members who can hold library cards and physical book copies to lend — but there is no way to actually lend them. This change delivers Phase 3 of the catalog-to-library evolution: a `Loan` entity with the borrow/return flow and business invariants, making the library functional end-to-end.

## What Changes

- **New slice `loans/`** with the `Loan` entity, `LoanService`, and five endpoints covering the full borrow/return lifecycle.
- **New action endpoints**: `POST /loans/{id}/return` (mark returned) and `DELETE /loans/{id}/return` (undo a mistaken return), plus `DELETE /loans/{id}` to cancel an active loan.
- **Loan status is derived**, not stored: `active`, `overdue`, and `returned` are computed from `returned_at` and `due_date` — no status column, no cron job.
- **`LoanService` orchestrates three repositories** (`LoanRepository`, `MemberRepository`, `BookCopyRepository`), enforcing business invariants at the application layer.
- **Two new settings** in `config.py` (`loan_period_days`, `loan_max_active`) make the loan period and per-member loan limit configurable via environment variable.
- **Delta to `book-management`**: `BookPublic` gains `copies_available: int` (deferred from Phase 2), derived via SQL aggregate — no extra queries.
- **Delta to `database-seeding`**: `seed.py` gains `SAMPLE_BOOK_COPIES` (missing from Phase 2) and `SAMPLE_LOANS` covering all three loan states.
- **Alembic migration**: reversible `CREATE TABLE loans` with FK constraints `ON DELETE RESTRICT` to both `members` and `book_copies`.

## Capabilities

### New Capabilities

- `lending`: The full loan lifecycle — borrow, return, undo return, cancel, list/filter/sort by derived status. Includes the `Loan` domain model, service invariants, action endpoints, and the Alembic migration.

### Modified Capabilities

- `book-management`: `BookPublic` gains `copies_available: int` — number of copies with no active loan. Requirement change: the book detail/list response now includes copy availability.
- `database-seeding`: `seed.py` gains two new blocks — `SAMPLE_BOOK_COPIES` (physical copies, missing from Phase 2) and `SAMPLE_LOANS` (one loan in each state). Idempotency is per-entity, seeding order is books → members → book_copies → loans.

## Impact

- **New code**: `src/app/loans/` (domain, application, infrastructure layers); Alembic migration file.
- **Modified code**: `src/app/books/infrastructure/sql_book_repository.py` (`copies_available` subquery); `src/app/books/domain/book_model.py` (`BookPublic`); `src/app/config.py` (two new settings); `scripts/seed.py` (two new blocks); `src/app/main.py` (router registration).
- **API surface**: Five new endpoints under `/loans`; `BookPublic` response schema gains one field.
- **No breaking changes** to existing endpoints.
