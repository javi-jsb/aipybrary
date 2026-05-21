## Why

With 4 implemented slices (`books`, `members`, `book_copies`, `loans`), a set of identical primitives is duplicated verbatim across every slice: factory functions, a sort-order enum, entity field declarations, a DB integrity helper, and a pagination envelope. The `lending` slice was the last planned stress test — now that it has landed without invalidating the patterns, it is the right moment to centralize these primitives and eliminate the drift risk.

## What Changes

- **New `src/app/core/` module** with:
  - `entity.py` — `_uuid7()`, `_utcnow()`, and `Entity` base class (`id` + `created_at` + `updated_at`)
  - `sorting.py` — shared `SortOrder(StrEnum)` enum
  - `db.py` — `is_constraint_violated(exc, constraint_name)` utility for named-constraint IntegrityError checks
  - `pagination.py` — `PaginatedResponse[T]` generic base with `pages` computed field
- **All 4 domain entity classes** (`Book`, `Member`, `BookCopy`, `Loan`) updated to inherit from `Entity` instead of declaring `id`/`created_at`/`updated_at` directly
- **All 4 domain model files** drop their local `SortOrder` definitions; all consumers (routers, repositories, fakes, tests) import `SortOrder` directly from `app.core.sorting`
- **All 4 SQL repositories** updated to use `is_constraint_violated()` from `core.db` and drop their private `_is_xxx_conflict()` helpers
- **All 4 `XxxListResponse` classes** updated to subclass `PaginatedResponse[XxxPublic]` (empty body, preserving concrete class names for OpenAPI)
- **New `tests/fakes/` module** with canonical in-memory fake repository implementations, shared across service tests and cross-slice tests
- **`alembic/env.py`** — add missing `app.loans.domain.loan_model` import (bug fix discovered during this work, tracked in #42)

## Capabilities

### New Capabilities

- `shared-primitives`: Internal engineering module (`src/app/core/` + `tests/fakes/`) that centralizes cross-slice utilities. No new HTTP endpoints or domain behavior — pure code organization.

### Modified Capabilities

*(none — all public API contracts, HTTP schemas, and domain behavior remain unchanged)*

## Impact

- **`src/app/`**: New `core/` package; all 4 domain model files, all 4 SQL repository files import from it
- **`tests/`**: New `fakes/` package; `test_book_service.py`, `test_book_copy_service.py`, `test_member_service.py`, `test_loan_service.py` import shared fakes
- **`alembic/env.py`**: One-line fix for missing loans model registration
- **Alembic**: Mandatory gold test — `alembic revision --autogenerate` must produce an empty migration after the Entity base refactor
- **No API changes**: Response schemas, endpoint paths, and domain exceptions are unchanged
- **Closes #25**, partially addresses #42 (Bug 1 / env.py fix only; Bug 2 / FK naming drift is out of scope)
