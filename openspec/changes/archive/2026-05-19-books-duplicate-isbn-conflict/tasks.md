## 1. Domain layer

- [x] 1.1 Create `src/app/books/domain/book_exceptions.py` with `DuplicateIsbnError` (docstring mirroring `member_exceptions.DuplicateEmailError`: repo translates the DB `IntegrityError`, router maps to 409)
- [x] 1.2 In `src/app/books/domain/book_model.py`: add `ISBN_CONSTRAINT = "uq_books_isbn"`, remove `unique=True` from the `isbn` `Field`, add `__table_args__ = (UniqueConstraint("isbn", name=ISBN_CONSTRAINT),)` (import `UniqueConstraint`), mirroring the `Member` model

## 2. Database migration

- [x] 2.1 Create a new Alembic revision chained off the current head `7f3a1c9d2b4e` (create members) — not `ca883df3f8a5`, which would fork the graph — that `upgrade`s with `op.drop_constraint("books_isbn_key", "books", type_="unique")` then `op.create_unique_constraint("uq_books_isbn", "books", ["isbn"])`, and `downgrade`s with the reverse
- [x] 2.2 Add an in-file comment in the migration explaining that `books_isbn_key` is Postgres' deterministic `<table>_<column>_key` default for the previously-unnamed constraint (answers "where does this name come from?")

## 3. Infrastructure layer

- [x] 3.1 In `sql_book_repository.py`: add `_is_isbn_conflict(exc)` helper (matches `ISBN_CONSTRAINT in str(exc.orig)`, docstring mirroring `_is_email_conflict`)
- [x] 3.2 Wrap `commit()` in `create` with `try/except IntegrityError`: on ISBN conflict `rollback()` + `raise DuplicateIsbnError from exc`; otherwise `raise` (propagate untouched)
- [x] 3.3 Apply the same `try/except` to `update`
- [x] 3.4 In `book_router.py`: catch `DuplicateIsbnError` in `create_book` and `update_book`, raising `HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ISBN already registered")` (module-level detail constant, mirroring `member_router`); preserve existing 404 ordering in `update_book`

## 4. Tests

- [x] 4.1 Repository test: `create`/`update` raise `DuplicateIsbnError` on a duplicate `isbn`, and a non-ISBN `IntegrityError` still propagates (not mislabelled 409)
- [x] 4.2 API test: `POST /books` with an existing `isbn` → `409`
- [x] 4.3 API test: `PATCH /books/{id}` setting `isbn` to another book's value → `409`; non-existent id still → `404` (existing `test_update_book_not_found`)
- [x] 4.4 API regression: distinct/`null` `isbn` creations still succeed (`201`); multiple `null` ISBNs allowed
- [x] 4.5 Migration test: applying the rename revision yields constraint `uq_books_isbn`; `downgrade` to `7f3a1c9d2b4e` reverts to `books_isbn_key`; re-upgrade restores it (real Postgres; reversibility test is sync to avoid the alembic/async-loop clash, mirroring `tests/members/test_member_migration.py`)

## 5. Verification

- [x] 5.1 `make check` (lint + format) clean
- [x] 5.2 `make coverage` — suite green (124 passed), coverage 100%
- [x] 5.3 Confirm no change to `members` slice and no new dependency in `pyproject.toml`/`uv.lock`
