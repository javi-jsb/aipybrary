## Why

Creating or updating a book with an `isbn` that already exists currently raises an
uncaught `IntegrityError`, which FastAPI surfaces as **500 Internal Server Error**.
This is a defect — a client-caused unique-constraint violation must be a `4xx`. The
`member-management` capability (now shipped) already maps a duplicate `email` to
**409 Conflict**, so `/books` and `/members` are inconsistent for the same class of
error. Closes the gap with a proper, consistent `409`.

## What Changes

- `POST /books` and `PATCH /books/{book_id}` return **409 Conflict** (not 500) when
  the submitted `isbn` collides with an existing book.
- The duplicate-ISBN `IntegrityError` is translated into a domain-level signal and
  mapped to HTTP `409` at the boundary, mirroring how `members` handles duplicate
  `email` — while preserving the precision the members slice deliberately built:
  any *other* `IntegrityError` (e.g. a NOT NULL violation) must still propagate
  untouched, not be mislabelled `409`.
- The books `isbn` unique constraint, currently **unnamed** (`sa.UniqueConstraint("isbn")`,
  Postgres default name `books_isbn_key`), is given an explicit name via a new
  Alembic migration so the SQL repository can discriminate the constraint reliably,
  consistent with `uq_members_email`.
- Not a breaking change: a behaviour that was an unhandled 500 becomes a defined 409.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `book-management`: the "Create a book" and "Update a book" requirements gain a
  duplicate-ISBN → `409` scenario; the "Books table migration" requirement gains a
  named unique constraint on `isbn` (so the repository can distinguish an ISBN
  collision from any other integrity violation, mirroring `uq_members_email`).

## Impact

- **Code:** `books/infrastructure/sql_book_repository.py` (catch + translate
  `IntegrityError` on `create`/`update`), `books/infrastructure/book_router.py`
  (map to `409`), a new books domain exception (e.g. `DuplicateIsbnError`), and the
  `isbn` constraint name in `books/domain/book_model.py`.
- **Migrations:** a new Alembic revision that renames the `isbn` unique constraint
  to an explicit name; reversible.
- **API contract:** `POST /books` and `PATCH /books/{book_id}` add a documented
  `409` response. No change to request/response bodies.
- **Cross-cutting decision (deferred to `design.md`):** per-router mapping (as
  `member-management` does) vs a shared app-level `IntegrityError → 409` handler
  for both `books` and `members`. Related to deferred shared-primitives work
  (issue #25) — adjacent but separable; do not pre-decide here.
