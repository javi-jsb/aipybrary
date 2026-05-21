## 1. Config & Settings

- [x] 1.1 Add `loan_period_days: int = Field(default=14)` to the Settings class in `src/app/config.py`
- [x] 1.2 Add `loan_max_active: int = Field(default=3)` to the Settings class in `src/app/config.py`

## 2. Domain Layer

- [x] 2.1 Create the `src/app/loans/` slice directory structure: `domain/`, `application/`, `infrastructure/`, and `__init__.py` files in each
- [x] 2.2 Define `LoanStatus` StrEnum (`active`, `overdue`, `returned`), `SortBy` StrEnum, `SortOrder` StrEnum, and `_uuid7` / `_utcnow` helpers in `src/app/loans/domain/loan_model.py`
- [x] 2.3 Define `Loan` SQLModel table class with fields: `id` (UUIDv7), `member_id` (FK `members.id` RESTRICT), `book_copy_id` (FK `book_copies.id` RESTRICT), `due_date`, `returned_at` (nullable), `created_at`, `updated_at`
- [x] 2.4 Define `LoanCreate` (member_id + book_copy_id only), `LoanPublic` (all fields + `@computed_field status: LoanStatus`), and `LoanListResponse` (paginated envelope with computed `pages`) schemas
- [x] 2.5 Define `LoanRepository` ABC in `src/app/loans/domain/loan_repository.py` with methods: `create`, `get_by_id`, `get_filtered`, `mark_returned`, `undo_return`, `delete`, `count_active_for_member`, `get_active_for_copy`
- [x] 2.6 Define all domain exceptions in `src/app/loans/domain/loan_exceptions.py`: `MemberNotFoundError`, `MemberSuspendedError`, `BookCopyNotFoundError`, `BookCopyNotAvailableError`, `LoanLimitExceededError`, `LoanAlreadyReturnedError`, `LoanNotReturnedError`, `LoanAlreadyReturnedCancelError`

## 3. Application Layer

- [x] 3.1 Implement `LoanService.__init__` in `src/app/loans/application/loan_service.py` receiving `LoanRepository`, `MemberRepository`, and `BookCopyRepository` via constructor injection
- [x] 3.2 Implement `LoanService.borrow(member_id, book_copy_id)` enforcing all five invariants in order: member exists → member active → copy exists → copy not on active loan → member under loan limit; compute `due_date = now() + timedelta(days=settings.loan_period_days)`
- [x] 3.3 Implement `LoanService.return_loan(loan_id)`: get by id (None → return None), check `returned_at IS NULL` (raise `LoanAlreadyReturnedError` if not), delegate to repo `mark_returned`
- [x] 3.4 Implement `LoanService.undo_return(loan_id)`: get by id (None → return None), check `returned_at IS NOT NULL` (raise `LoanNotReturnedError` if null), delegate to repo `undo_return`
- [x] 3.5 Implement `LoanService.cancel(loan_id)`: get by id (None → return False), check `returned_at IS NULL` (raise `LoanAlreadyReturnedCancelError` if set), delegate to repo `delete`; return True
- [x] 3.6 Implement `LoanService.get_by_id(loan_id)` and `LoanService.get_filtered(member_id, book_copy_id, status, sort_by, order, page, size)` returning a `LoanListResponse`

## 4. Infrastructure Layer

- [x] 4.1 Implement `SqlModelLoanRepository` in `src/app/loans/infrastructure/sql_loan_repository.py` with `create`, `get_by_id`, `delete`, `count_active_for_member`, and `get_active_for_copy` methods
- [x] 4.2 Implement `SqlModelLoanRepository.mark_returned` (sets `returned_at = now()`, triggers `updated_at`), and `undo_return` (sets `returned_at = None`, triggers `updated_at`)
- [x] 4.3 Implement `SqlModelLoanRepository.get_filtered` with SQL predicates for the `status` filter (`active`: `returned_at IS NULL AND due_date >= now()`; `overdue`: `returned_at IS NULL AND due_date < now()`; `returned`: `returned_at IS NOT NULL`), all sort options, and count + slice pagination
- [x] 4.4 Implement `loan_router.py` in `src/app/loans/infrastructure/loan_router.py` with `_get_service` factory (injecting all three concrete repos) and `ServiceDep` alias
- [x] 4.5 Add `GET /loans` endpoint (list with all filter and sort query params, returns `LoanListResponse`)
- [x] 4.6 Add `GET /loans/{loan_id}` endpoint (returns `LoanPublic`, 404 if not found)
- [x] 4.7 Add `POST /loans` endpoint (borrow; maps exceptions to 404/422/409 as per spec)
- [x] 4.8 Add `POST /loans/{loan_id}/return` endpoint (maps `LoanAlreadyReturnedError` → 409, returns updated `LoanPublic`)
- [x] 4.9 Add `DELETE /loans/{loan_id}/return` endpoint (undo return; maps `LoanNotReturnedError` → 409, returns updated `LoanPublic`)
- [x] 4.10 Add `DELETE /loans/{loan_id}` endpoint (cancel; maps `LoanAlreadyReturnedCancelError` → 409, returns 204 on success)
- [x] 4.11 Register the loan router in `src/app/main.py`

## 5. Alembic Migration

- [x] 5.1 Author Alembic migration: `CREATE TABLE loans` with all columns, named FK constraints (`fk_loans_member_id_members` ON DELETE RESTRICT, `fk_loans_book_copy_id_book_copies` ON DELETE RESTRICT), and indexes on `member_id` and `book_copy_id`
- [x] 5.2 Verify the migration round-trips cleanly: `make db-migrate` (`upgrade head`), then manual `alembic downgrade -1`, then `make db-migrate` again

## 6. Book Management Delta

- [x] 6.1 Add `copies_available: int` field to `BookPublic` in `src/app/books/domain/book_model.py`
- [x] 6.2 Add `copies_available` correlated subquery to `sql_book_repository.py` alongside the existing `copies_total` logic — import `Loan` from `app.loans.domain.loan_model` and use `col(Loan.book_copy_id)` / `col(Loan.returned_at)` directly, counting copies where no active loan (`returned_at IS NULL`) exists

## 7. Seeding

- [x] 7.1 Add `SAMPLE_BOOK_COPIES` list to `scripts/seed.py` with at least 5 copies across at least 3 books (look up book IDs after inserting books; use unique barcodes)
- [x] 7.2 Add `SAMPLE_LOANS` logic to `scripts/seed.py` covering all three states: at least 1 active (due_date in future), 1 overdue (due_date in past, returned_at None), 1 returned (returned_at set)
- [x] 7.3 Update the `seed()` function to call all four blocks in order and add the book_copies + loans idempotency checks (skip each block if records already exist)

## 8. Tests

- [x] 8.1 Write unit tests for `Loan` domain model: `LoanStatus` computation for all three states, field defaults, `LoanPublic.status` computed field — in `tests/loans/test_loan_model.py`
- [x] 8.2 Write unit tests for `LoanService` with mocked repositories covering all invariant paths in `borrow()` (5 error cases + success) — in `tests/loans/test_loan_service.py`
- [x] 8.3 Write unit tests for `LoanService.return_loan()`, `undo_return()`, and `cancel()` including success and error paths
- [x] 8.4 Write integration tests for `POST /loans`: success (201), member not found (404), suspended member (422), copy not found (404), copy already on loan (409), loan limit exceeded (422) — in `tests/loans/test_loan_router.py`
- [x] 8.5 Write integration tests for `POST /loans/{id}/return`: success (200), not found (404), already returned (409)
- [x] 8.6 Write integration tests for `DELETE /loans/{id}/return`: success (200), not found (404), not returned (409)
- [x] 8.7 Write integration tests for `DELETE /loans/{id}`: success (204), not found (404), already returned (409)
- [x] 8.8 Write integration tests for `GET /loans`: default pagination, filter by `member_id`, filter by `book_copy_id`, filter by each `status` value, sort by `due_date` and `returned_at`
- [x] 8.9 Write integration tests for `GET /loans/{id}`: found (200 with correct computed `status`), not found (404)
- [x] 8.10 Write integration tests for `copies_available` in `GET /books` and `GET /books/{id}`: reflects active loans, treats returned loans as available
- [x] 8.11 Run `make test` and `make coverage`; ensure near-100% coverage with `# pragma: no cover` only for genuinely untestable lines
