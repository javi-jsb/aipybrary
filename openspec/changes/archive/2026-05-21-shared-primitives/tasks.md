## 1. Create src/app/core/ module

- [x] 1.1 Create `src/app/core/__init__.py` (empty)
- [x] 1.2 Create `src/app/core/entity.py` with `_uuid7()`, `_utcnow()`, and `Entity` base class (`id` + `created_at` + `updated_at`, not `table=True`)
- [x] 1.3 Create `src/app/core/sorting.py` with shared `SortOrder(StrEnum)` enum (`asc`, `desc`)
- [x] 1.4 Create `src/app/core/db.py` with `constraint_violated(exc: IntegrityError, constraint_name: str) -> bool`
- [x] 1.5 Create `src/app/core/pagination.py` with `PaginatedResponse[T]` generic (`items`, `total`, `page`, `size`, `pages` computed field)

## 2. Migrate domain models to Entity base and shared SortOrder

- [x] 2.1 Update `books/domain/book_model.py`: inherit `Book` from `Entity`, remove local `_uuid7`/`_utcnow`/`id`/`created_at`/`updated_at`, import `SortOrder` from `app.core.sorting`
- [x] 2.2 Update `members/domain/member_model.py`: same — inherit `Member` from `Entity`, remove local helpers, import `SortOrder`
- [x] 2.3 Update `book_copies/domain/book_copy_model.py`: same — inherit `BookCopy` from `Entity`, remove local helpers, import `SortOrder`
- [x] 2.4 Update `loans/domain/loan_model.py`: same — inherit `Loan` from `Entity`, remove local helpers, import `SortOrder`
- [x] 2.5 Run `alembic revision --autogenerate -m "test-entity-base"` and verify the migration body is empty (gold test) — then delete the test migration file

## 3. Migrate SQL repositories to constraint_violated()

- [x] 3.1 Update `books/infrastructure/sql_book_repository.py`: replace `_is_isbn_conflict()` and `_is_book_copies_fk_conflict()` with inline `constraint_violated()` calls, import from `app.core.db`
- [x] 3.2 Update `members/infrastructure/sql_member_repository.py`: replace `_is_email_conflict()` with inline `constraint_violated()`, import from `app.core.db`
- [x] 3.3 Update `book_copies/infrastructure/sql_book_copy_repository.py`: replace `_is_barcode_conflict()` and any FK conflict helpers with `constraint_violated()`, import from `app.core.db`

## 4. Migrate list response classes to PaginatedResponse[T]

- [x] 4.1 Update `books/domain/book_model.py`: replace `BookListResponse` body with `class BookListResponse(PaginatedResponse[BookPublic]): pass`
- [x] 4.2 Update `members/domain/member_model.py`: replace `MemberListResponse` body with `class MemberListResponse(PaginatedResponse[MemberPublic]): pass`
- [x] 4.3 Update `book_copies/domain/book_copy_model.py`: replace `BookCopyListResponse` body with `class BookCopyListResponse(PaginatedResponse[BookCopyPublic]): pass`
- [x] 4.4 Update `loans/domain/loan_model.py`: replace `LoanListResponse` body with `class LoanListResponse(PaginatedResponse[LoanPublic]): pass`

## 5. Fix alembic/env.py missing loans import

- [x] 5.1 Add `import app.loans.domain.loan_model  # noqa: F401` to `alembic/env.py` alongside the other model imports

## 6. Create canonical test fakes in tests/fakes/

- [x] 6.1 Create `tests/fakes/__init__.py` (empty)
- [x] 6.2 Create `tests/fakes/book_fakes.py` with `FakeBookRepository` — full implementation with `add()` and `set_copies(book_id, n)` helpers
- [x] 6.3 Create `tests/fakes/member_fakes.py` with `FakeMemberRepository` — full implementation with `add()` helper
- [x] 6.4 Create `tests/fakes/book_copy_fakes.py` with `FakeBookCopyRepository` — full implementation with `add()` helper
- [x] 6.5 Create `tests/fakes/loan_fakes.py` with `FakeLoanRepository` — full implementation with `add()` and `set_active_count()` helpers

## 7. Update test files to use shared fakes

- [x] 7.1 Update `tests/books/test_book_service.py`: import `FakeBookRepository` from `tests.fakes.book_fakes`, remove local class definition
- [x] 7.2 Update `tests/book_copies/test_book_copy_service.py`: import `FakeBookRepository` from `tests.fakes.book_fakes` and `FakeBookCopyRepository` from `tests.fakes.book_copy_fakes`, remove local class definitions
- [x] 7.3 Update `tests/members/test_member_service.py`: import `FakeMemberRepository` from `tests.fakes.member_fakes`, remove local class definition
- [x] 7.4 Update `tests/loans/test_loan_service.py`: import all three fakes (`FakeMemberRepository`, `FakeBookCopyRepository`, `FakeLoanRepository`) from `tests.fakes`, remove all local class definitions

## 8. Verify

- [x] 8.1 Run `make test` — full suite passes
- [x] 8.2 Run `make coverage` — near 100%, no `# pragma: no cover` in `tests/fakes/`
- [x] 8.3 Run `make check` — no lint or format errors
