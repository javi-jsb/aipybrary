## Why

aipybrary is evolving from a book catalog into a lending library. Loans (Phase 3) need to reference **physical copies**, not titles — two patrons can borrow two different copies of the same book at the same time. Phase 2 introduces the `BookCopy` entity (a physical instance of a `Book`) so that Phase 3 can model `Loan` against concrete inventory rather than abstract titles.

## What Changes

- New entity `BookCopy` with fields `id`, `book_id` (FK to books), `barcode` (required, unique), `location` (optional), `notes` (optional), `created_at`, `updated_at`. No `status` field in this phase — physical condition is out of scope; "currently lent" will be derived from `Loan` in Phase 3.
- New domain layer: `BookCopy` SQLModel entity, `BookCopyRepository` ABC, `BookCopyCreate` / `BookCopyUpdate` / `BookCopyPublic` / `BookCopyListResponse` schemas, `DuplicateBarcodeError` domain exception.
- New application layer: `BookCopyService` that orchestrates the `BookCopyRepository` and the existing `BookRepository` (to validate that `book_id` references an existing book at creation time).
- New infrastructure layer: `SqlModelBookCopyRepository`, `book_copy_router` exposing flat REST routes under `/book-copies`.
- New Alembic migration: creates the `book_copies` table with a named unique constraint `uq_book_copies_barcode` and a FK to `books.id` with `ON DELETE RESTRICT`.
- **Modified behaviour in `book-management`**: `DELETE /books/{book_id}` SHALL return `409 Conflict` when the book has at least one copy (DB enforces `RESTRICT`, repository translates the `IntegrityError`).
- **Modified shape in `book-management`**: `BookPublic` SHALL gain a derived `copies_total: int` field calculated at query time via a single aggregated SQL statement (no N+1). `copies_available` is deliberately deferred to Phase 3 when `Loan` exists.

## Capabilities

### New Capabilities

- `book-copy-management`: CRUD plus paginated/filterable/sortable listing of `BookCopy` (a physical instance of a `Book`), including the domain model, barcode uniqueness, repository abstraction, application service with cross-slice book existence validation, HTTP endpoints, and the database migration.

### Modified Capabilities

- `book-management`: `DELETE /books/{book_id}` now returns `409` when copies exist (enforced via FK `ON DELETE RESTRICT`); `BookPublic` gains a derived `copies_total` field surfaced in `GET /books` and `GET /books/{book_id}`.

## Impact

- **New code**: `src/app/book_copies/` slice (`domain/`, `application/`, `infrastructure/`), mirroring the structure of `src/app/members/`. Cross-slice import is allowed at the **service** layer only (`BookCopyService` imports `BookRepository` ABC for orchestration); domain entities reference foreign aggregates by ID only (`BookCopy.book_id: UUID`, no `Book` import).
- **Modified code**: `src/app/books/domain/book_model.py` (add `copies_total` to `BookPublic`), `src/app/books/domain/book_repository.py` (extend repo contract or add aggregated query), `src/app/books/infrastructure/sql_book_repository.py` (DELETE → translate `IntegrityError` to `BookHasCopiesError` or equivalent → 409 in router; list/get queries to include `copies_total` aggregation), `src/app/books/infrastructure/book_router.py` (map 409).
- **Migrations**: one new Alembic revision creating the `book_copies` table; reversible.
- **Routing**: new `/book-copies` flat resource registered in the FastAPI app, consistent with `/books` and `/members`.
- **Helpers duplicated a third time** (`_uuid7`, `_utcnow`, `SortOrder`, `ListResponse` envelope, `Duplicate<X>Error` pattern). This is intentional — issue #25 will unify shared primitives later; repeating once more is not new debt.
- **No breaking API changes**: `BookPublic` adding `copies_total` is additive. The DELETE behavior change is a new error case for an existing endpoint, not a change to its success path.
- **Tests**: new unit tests (domain validators, schemas, service with fake repo) and new integration tests (router + real DB) for the `book_copies` slice; new integration scenarios in `books/` for the DELETE-409 case and the `copies_total` field.
