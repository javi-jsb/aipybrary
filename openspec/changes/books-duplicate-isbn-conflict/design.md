## Context

`POST /books` and `PATCH /books/{book_id}` currently let a duplicate-`isbn`
`IntegrityError` propagate uncaught. `SqlModelBookRepository.create/update` have
no `except IntegrityError` block (unlike `SqlModelMemberRepository`), so FastAPI
returns **500** for a client-caused unique-constraint violation — a defect.

The `member-management` capability (shipped, archived `2026-05-19-member-management`)
already solves the equivalent problem for `email`:

- `member_model.py`: `EMAIL_CONSTRAINT = "uq_members_email"` + `__table_args__ =
  (UniqueConstraint("email", name=EMAIL_CONSTRAINT),)` (no field-level `unique=True`).
- `sql_member_repository.py`: `_is_email_conflict(exc)` matches the constraint name
  in `str(exc.orig)`, raises domain `DuplicateEmailError`; **any other**
  `IntegrityError` propagates untouched (so a NOT NULL violation is not
  mislabelled `409`).
- `member_router.py`: catches `DuplicateEmailError` → `HTTPException(409, ...)`.
- Migration `7f3a1c9d2b4e`: `sa.UniqueConstraint("email", name="uq_members_email")`
  — a literal string, no domain import.

`books` is asymmetric: `book_model.py` uses field-level `Field(..., unique=True)`
with **no constraint name and no constant**, and migration `1ba646289ba0` emits an
unnamed `sa.UniqueConstraint("isbn")`. Postgres therefore assigns its default name
`books_isbn_key` (`<table>_<column>_key`) — an implicit name nothing in the
codebase documents.

## Goals / Non-Goals

**Goals:**
- `POST /books` and `PATCH /books/{book_id}` return `409` (not `500`) on a
  duplicate `isbn`.
- Preserve the discrimination precision `members` built: only the ISBN
  unique-constraint violation becomes `409`; every other `IntegrityError` keeps
  propagating.
- Make the `isbn` constraint name explicit and discoverable in the codebase
  (constant in the model + literal in the migration), mirroring `uq_members_email`.

**Non-Goals:**
- No shared/app-level `IntegrityError` handler; the shipped `members` slice is
  not refactored (see Decision 1).
- No change to request/response bodies, ISBN validation, or any other endpoint.
- Resolving the broader cross-slice shared-primitives question (issue #25) — this
  change is deliberately one more data point for that, not its resolution.

## Decisions

### Decision 1 — Per-slice mapping, mirroring `members` (not a shared handler)

Replicate the `members` pattern inside the `books` slice:

- New `books/domain/book_exceptions.py` → `DuplicateIsbnError`.
- `SqlModelBookRepository.create` and `.update` wrap `commit()` in
  `try/except IntegrityError`: on `ISBN_CONSTRAINT in str(exc.orig)`, `rollback()`
  then `raise DuplicateIsbnError from exc`; otherwise `raise` (propagate).
- `book_router.py` `create_book` / `update_book` catch `DuplicateIsbnError` →
  `HTTPException(status_code=409, detail="ISBN already registered")`.

**Why over a shared app-level handler:** the shared `IntegrityError → 409`
handler is the cleaner long-term shape, but it is a cross-cutting refactor that
modifies the already-shipped `members` slice and would pull the deferred #25
decision forward. A naive global handler would also *regress* the precision
`members` deliberately built unless it carries a constraint-name registry — extra
infrastructure this small fix does not justify. Keeping the per-slice pattern
makes `books` consistent with the only existing precedent and turns the
duplication into the third concrete data point that informs #25 (the
"improve-then-backport-separately" precedent), rather than pre-deciding it.

### Decision 2 — Name the `isbn` constraint `uq_books_isbn` via a new migration

Mirror the `members` modelling exactly:

- `book_model.py`: add `ISBN_CONSTRAINT = "uq_books_isbn"`; remove `unique=True`
  from the `isbn` `Field`; add `__table_args__ = (UniqueConstraint("isbn",
  name=ISBN_CONSTRAINT),)`. (Field-level `unique=True` is dropped so there is
  exactly one unique constraint, exactly as `members` does.)
- New Alembic revision (head after `ca883df3f8a5`): `op.drop_constraint(
  "books_isbn_key", "books", type_="unique")` then `op.create_unique_constraint(
  "uq_books_isbn", "books", ["isbn"])`; `downgrade` reverses it.
- The migration repeats the literal `"uq_books_isbn"` (no domain import — same
  convention as `members`), and carries an in-file comment explaining that
  `books_isbn_key` is Postgres' deterministic `<table>_<column>_key` default for
  the previously-unnamed constraint, so "where does this name come from?" is
  answered in the code.

**Why not edit the original create-books migration:** the `books` table already
exists in any migrated database with the auto-named `books_isbn_key`; rewriting
revision `1ba646289ba0` would break the migration history and not affect existing
databases. A forward, reversible rename migration is the only correct option.

**Why not just hard-code `books_isbn_key` in the constant:** it works, but
perpetuates exactly the undiscoverable implicit-name problem this change exists
to fix; it also diverges from the `uq_members_email` convention.

## Risks / Trade-offs

- **The rename migration assumes the existing constraint is named
  `books_isbn_key`.** → That is Postgres' deterministic default for an unnamed
  single-column `UNIQUE` (`<table>_<column>_key`); the books table has exactly one
  such constraint. Documented in the migration; verified by the migration's own
  reversibility test on a real Postgres (Docker), consistent with how the
  members-migration test works.
- **Conscious slice-local duplication of the `IntegrityError`-translation
  pattern** (now 2×: members, books). → Accepted and intended: it is the input
  to the deferred shared-primitives exploration (#25), not debt to hide.
- **`detail` string ("ISBN already registered") is slice-local**, like
  `members`' "Email already registered". → Acceptable; consolidating message
  conventions is part of the same future #25 discussion.

## Migration Plan

1. Ship code + the new Alembic revision together in one change.
2. Deploy: `alembic upgrade head` performs the constraint rename online
   (drop+create on a single column; brief lock, negligible at this scale).
3. Rollback: `alembic downgrade -1` restores the unnamed `books_isbn_key`; the
   pre-change code (field-level `unique=True`) remains compatible with it.

## Open Questions

None blocking. The shared app-level handler vs per-slice consolidation remains
deliberately open under issue #25 and is explicitly out of scope here.
