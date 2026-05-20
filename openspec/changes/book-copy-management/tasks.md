## 1. Slice scaffolding

- [ ] 1.1 Create `src/app/book_copies/` with `__init__.py` and subdirectories `domain/`, `application/`, `infrastructure/` (each with `__init__.py`)
- [ ] 1.2 Mirror the package layout used in `src/app/members/` so the conventions match

## 2. Domain layer — BookCopy model and schemas

- [ ] 2.1 Create `src/app/book_copies/domain/book_copy_model.py` with helpers `_uuid7()` and `_utcnow()` (third deliberate duplication, tracked by issue #25)
- [ ] 2.2 Define `SortBy` (`barcode`, `location`, `created_at`) and `SortOrder` (`asc`, `desc`) as `StrEnum`s
- [ ] 2.3 Define `BookCopy` SQLModel table with fields `id`, `book_id` (UUID, NOT NULL), `barcode` (str, max 100, NOT NULL), `location` (str | None, max 200), `notes` (str | None, TEXT), `created_at`, `updated_at`
- [ ] 2.4 Declare named unique constraint `uq_book_copies_barcode` via `__table_args__`
- [ ] 2.5 Confirm `BookCopy` imports nothing from `src/app/books/` (referential link is only `book_id: UUID`)
- [ ] 2.6 Define Pydantic schemas `BookCopyCreate`, `BookCopyUpdate` (without `book_id`), `BookCopyPublic`
- [ ] 2.7 Define `BookCopyListResponse` envelope with `items`, `total`, `page`, `size`, computed `pages` (mirror of `MemberListResponse`)

## 3. Domain layer — repository contract and exceptions

- [ ] 3.1 Create `src/app/book_copies/domain/book_copy_repository.py` defining `BookCopyRepository` ABC with abstract methods `create`, `get_by_id`, `get_paginated`, `update`, `delete`, `count_by_book_id`
- [ ] 3.2 Document `get_paginated` signature accepting filter args (`book_id`, `barcode`, `location`) and sort args (`sort_by`, `order`)
- [ ] 3.3 Create `src/app/book_copies/domain/book_copy_exceptions.py` with `DuplicateBarcodeError` and `BookCopyBookNotFoundError` (or equivalent name) for the cross-slice validation failure

## 4. Infrastructure layer — Alembic migration

- [ ] 4.1 Generate a new Alembic revision (timestamped) named e.g. `create_book_copies_table`
- [ ] 4.2 Implement `upgrade()` to create `book_copies` table with all columns, FK to `books.id ON DELETE RESTRICT`, named unique constraint `uq_book_copies_barcode`, server defaults for timestamps
- [ ] 4.3 Add an explicit index on `book_id` for FK lookups and `copies_total` aggregation
- [ ] 4.4 Implement `downgrade()` to drop the table
- [ ] 4.5 Verify migration runs both ways (`alembic upgrade head` then `alembic downgrade -1` then `alembic upgrade head`) on a local Postgres instance

## 5. Infrastructure layer — SQL repository

- [ ] 5.1 Create `src/app/book_copies/infrastructure/sql_book_copy_repository.py` implementing all `BookCopyRepository` methods using async SQLModel sessions
- [ ] 5.2 In `create` and `update`, catch `IntegrityError`, inspect the constraint name, and re-raise as `DuplicateBarcodeError` when `uq_book_copies_barcode` is violated; re-raise other integrity errors unchanged
- [ ] 5.3 Implement `get_paginated` to apply `book_id` exact match, `barcode` and `location` `ILIKE` filters, the sort fields, and pagination (`offset`/`limit`), returning the list and a `total` count
- [ ] 5.4 Implement `count_by_book_id` using `SELECT COUNT(*)` filtered by `book_id`

## 6. Application layer — service

- [ ] 6.1 Create `src/app/book_copies/application/book_copy_service.py` defining `BookCopyService` that receives `book_copy_repo: BookCopyRepository` and `book_repo: BookRepository` via constructor injection
- [ ] 6.2 Implement `create(data)` that first calls `book_repo.get_by_id(data.book_id)`; if `None`, raise the cross-slice validation exception; otherwise delegate to `book_copy_repo.create(data)`
- [ ] 6.3 Implement `get_by_id`, `get_paginated`, `update`, `delete` delegating to `book_copy_repo`
- [ ] 6.4 Verify the service has no SQLModel or FastAPI imports

## 7. Infrastructure layer — HTTP router

- [ ] 7.1 Create `src/app/book_copies/infrastructure/book_copy_router.py` exposing the FastAPI router under prefix `/book-copies`
- [ ] 7.2 Wire dependency injection so the router receives a `BookCopyService` (which itself receives `SqlModelBookCopyRepository` and the existing `SqlModelBookRepository`)
- [ ] 7.3 Implement `POST /book-copies` returning 201; map the cross-slice validation exception to `422`, map `DuplicateBarcodeError` to `409`
- [ ] 7.4 Implement `GET /book-copies` with query params `page`, `size`, `book_id`, `barcode`, `location`, `sort_by`, `order`, returning `BookCopyListResponse`
- [ ] 7.5 Implement `GET /book-copies/{copy_id}` returning 200 or 404
- [ ] 7.6 Implement `PATCH /book-copies/{copy_id}` returning 200/404; map `DuplicateBarcodeError` to `409`
- [ ] 7.7 Implement `DELETE /book-copies/{copy_id}` returning 204 or 404
- [ ] 7.8 Register the router in the FastAPI app entry point (same place where `books_router` and `members_router` are mounted)

## 8. Modify `books` slice — DELETE 409 and copies_total

- [ ] 8.1 Add `BookHasCopiesError` (or equivalent name) to `src/app/books/domain/book_exceptions.py`
- [ ] 8.2 In `SqlModelBookRepository.delete`, catch `IntegrityError` and, when the failure is the FK from `book_copies.book_id`, re-raise as `BookHasCopiesError`; re-raise other integrity errors unchanged
- [ ] 8.3 In `book_router`, map `BookHasCopiesError` to `409 Conflict`
- [ ] 8.4 Extend `BookPublic` to include `copies_total: int`
- [ ] 8.5 Modify `SqlModelBookRepository.get_by_id` and `get_paginated` to compute `copies_total` per book via a single aggregated query (correlated subquery or `LEFT JOIN ... GROUP BY`)
- [ ] 8.6 Ensure no N+1 — verify by enabling SQL echo locally and confirming the total query count for `GET /books` is bounded

## 9. Tests — `book_copies` slice

- [ ] 9.1 Add a `conftest.py` under the book_copies test path with fixtures for `BookCopyRepository` fakes and HTTP client setup
- [ ] 9.2 Domain unit tests: `BookCopy` model invariants, `BookCopyCreate` validation (required fields, max lengths), `BookCopyUpdate` rejects `book_id`
- [ ] 9.3 Service unit tests with a fake `BookRepository` and fake `BookCopyRepository`: book exists → delegates; book missing → raises validation; standard CRUD delegations
- [ ] 9.4 Integration tests for `POST /book-copies`: 201 happy path, 422 missing fields, 422 non-existent book_id, 409 duplicate barcode
- [ ] 9.5 Integration tests for `GET /book-copies`: default pagination on empty/populated DB, second page, page=0/size=101 → 422, filter by `book_id`/`barcode`/`location`, invalid UUID for `book_id` → 422, combined filters, no-match returns empty
- [ ] 9.6 Integration tests for sort: by `barcode` asc, default `created_at` desc, invalid `sort_by` → 422
- [ ] 9.7 Integration tests for `GET /book-copies/{copy_id}`: 200 and 404
- [ ] 9.8 Integration tests for `PATCH /book-copies/{copy_id}`: partial update, 404, 409 on duplicate barcode, 422 if body includes `book_id`
- [ ] 9.9 Integration tests for `DELETE /book-copies/{copy_id}`: 204 success and 404 not found

## 10. Tests — `books` slice deltas

- [ ] 10.1 Integration test: `DELETE /books/{book_id}` returns `204` when the book has zero copies
- [ ] 10.2 Integration test: `DELETE /books/{book_id}` returns `409` when the book has at least one copy, and the book remains retrievable afterwards
- [ ] 10.3 Integration test: `GET /books` returns `copies_total` correctly for books with 0, 1, and N copies
- [ ] 10.4 Integration test: `GET /books/{book_id}` returns `copies_total` for a specific book
- [ ] 10.5 Integration test (or SQL trace): confirm `GET /books` query count does not grow linearly with the number of books

## 11. Docs and housekeeping

- [ ] 11.1 Confirm `make check` (lint + format) passes
- [ ] 11.2 Confirm `make test` passes and coverage stays near 100% (use `# pragma: no cover` only for DI wiring or true abstract stubs)
- [ ] 11.3 Update README if any developer-facing command changed (likely not)
- [ ] 11.4 Verify `CLAUDE.md` does not need updates (this change does not introduce new conventions; the cross-slice layer table is captured in `design.md` and the project memory)
