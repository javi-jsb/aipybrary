## Context

The project has 4 vertical slices (`books`, `members`, `book_copies`, `loans`), each with its own domain, application, and infrastructure layers. The architecture is deliberately duplicative — slices were built verbatim from each other to avoid premature abstraction. Now that 4 slices exist and `lending` has landed as the final stress-test slice, the duplication inventory is stable and safe to consolidate.

Duplication points and their counts before this change:
- `_uuid7()` + `_utcnow()` factory functions: 4× identical
- `SortOrder(StrEnum)` enum: 4× identical
- `id` / `created_at` / `updated_at` Field declarations: 4× identical (8 lines each, ~32 total)
- `_is_xxx_conflict(exc)` private helpers in SQL repos: 3× structurally identical (loans has no unique constraint)
- `XxxListResponse` pagination envelope + `pages` computed field: 4× near-identical (only `items` type differs)
- `FakeMemberRepository` / `FakeBookCopyRepository` in tests: 2× each (full in slice tests, lean stubs in loan service test)

A secondary bug also exists: `alembic/env.py` never registered `loan_model`, so `autogenerate` would drop the `loans` table. This is fixed in the same PR (tracked in #42, Bug 1).

## Goals / Non-Goals

**Goals:**
- Introduce `src/app/core/` as the canonical home for cross-slice utilities
- Eliminate verbatim duplication of factory functions, `SortOrder`, Entity fields, IntegrityError helper, and pagination envelope
- Introduce `tests/fakes/` as the canonical home for shared in-memory repository fakes
- Fix the missing `loan_model` import in `alembic/env.py`
- Guarantee zero schema drift: `alembic revision --autogenerate` produces an empty migration after the refactor

**Non-Goals:**
- No new HTTP endpoints or domain behavior
- No changes to `SortBy` enums (legitimately per-slice)
- No `Repository(ABC)` base class (no second implementation exists, deferred)
- No `get_filtered` SQL scaffold helper (books' subquery projection breaks generalization)
- No fix for FK naming drift in autogenerate (Bug 2 of #42, separate investigation needed)

## Decisions

### D1 — `Entity` base with `id` + `created_at` + `updated_at` (Option B over Option A)

Option A was a `TimestampMixin` with only `created_at`/`updated_at`, leaving `id` per-slice. Option B is an `Entity` base that includes `id` as well.

**Chose Option B** because: all 4 entities use the same `id` strategy (`uuid7`, `primary_key=True`) without exception. Option A would still leave 4 identical `id` declarations. Option B gives a single change point if the PK strategy ever changes, and the evidence from 4 slices makes the "uuid7 PK for all entities" commitment explicit rather than accidental.

The base class must NOT be `table=True`. Entities inherit with `class Book(Entity, table=True)`. `__table_args__` stays in the subclass (no conflict). DTOs (`XCreate`, `XUpdate`, `XPublic`) do NOT inherit from `Entity` — they stay as plain `SQLModel` subclasses.

### D2 — Named concrete subclasses for `PaginatedResponse[T]` (over type aliases)

`BookListResponse = PaginatedResponse[BookPublic]` (alias) would cause FastAPI to emit `PaginatedResponse_BookPublic_` in the OpenAPI schema component name. Using a named subclass `class BookListResponse(PaginatedResponse[BookPublic]): pass` preserves the original component name in the OpenAPI spec, keeping the API contract unchanged for any client reading the schema.

### D3 — `is_constraint_violated()` utility in `core/db.py` (over app-level IntegrityError handler)

The broader option was a global `IntegrityError → 409` FastAPI exception handler. Chose the narrower utility function because: it preserves the per-slice domain exception hierarchy (`DuplicateEmailError`, `DuplicateIsbnError`, etc.), avoids coupling the handler to all constraint names app-wide, and the change is minimal — just deleting private functions and inlining the call. The `is_` prefix was added for clarity as a predicate function.

### D4 — `tests/fakes/` separate module (over `conftest.py`)

`conftest.py` is for pytest fixtures (session scoping, setup/teardown). Fake repositories are plain classes, not fixtures. A separate `tests/fakes/` module is more explicit, importable by name, and keeps `conftest.py` focused on fixture wiring. Naming: one file per slice domain (`book_fakes.py`, `member_fakes.py`, `book_copy_fakes.py`, `loan_fakes.py`).

### D5 — Flat files in `src/app/core/` (over a single `core.py`)

One file per concern (`entity.py`, `sorting.py`, `db.py`, `pagination.py`) keeps each file small and the import paths self-documenting (`from app.core.entity import Entity`). A single `core.py` would grow into an unrelated grab-bag.

**Critical constraint:** `src/app/core/` must never import from any slice (`app.books`, `app.members`, etc.). The dependency direction is strictly: slices → core, never core → slices.

## Risks / Trade-offs

- **SQLModel inheritance quirks with `table=True`** → Alembic gold test (`autogenerate` must produce empty migration) is the gate. Run it before declaring the Entity refactor complete. Also run the full test suite after each model change.

- **Field ordering change in `model_dump()`** → Inherited fields from `Entity` appear first. DTOs are unaffected (they don't inherit). Table entity serialization order changes but no slice logic depends on dict key order.

- **Import cycle risk** → `core/` files may only import from the stdlib, SQLModel, SQLAlchemy, and `uuid_utils`. Any import from a slice module is a bug. Enforce by convention; a future linter rule could formalize this.

- **`FakeBookRepository` has two distinct uses** → The books service test needs `set_copies()` to simulate `BookWithCounts` counts; the book_copies service test just needs `get_by_id`. The canonical fake will include `set_copies()` — the book_copies test simply won't call it. No behavioral difference.

## Migration Plan

1. Create `src/app/core/` with all utility modules
2. Refactor models slice by slice (entity inheritance + SortOrder import) — run `make test` after each slice
3. After all 4 models refactored: run `alembic revision --autogenerate` — must be empty
4. Refactor SQL repos to use `constraint_violated()`
5. Refactor `XxxListResponse` to subclass `PaginatedResponse[T]`
6. Fix `alembic/env.py` loans import
7. Create `tests/fakes/` with canonical fakes
8. Update all test files to import from `tests/fakes/`
9. Run `make test` + `make coverage` — full suite must pass at near-100% coverage

No database migrations needed. No rollback strategy required — this is a pure code refactor with no schema or API changes.

## Open Questions

*(none — all decisions resolved during pre-proposal exploration and debate)*
