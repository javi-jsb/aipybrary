## ADDED Requirements

### Requirement: Entity base class centralizes id and timestamp fields
The system SHALL provide an `Entity` base class in `src/app/core/entity.py` that is NOT a database table itself (`table=True` must not be set on it). It SHALL declare three fields: `id` (UUID v7, primary key), `created_at` (UTC datetime, server default `now()`), and `updated_at` (UTC datetime, server default `now()`, updated on write). All domain entity classes (`Book`, `Member`, `BookCopy`, `Loan`) SHALL inherit from `Entity` with `table=True` and SHALL NOT redeclare `id`, `created_at`, or `updated_at`.

#### Scenario: Entity subclass has id and timestamps without redeclaring them
- **WHEN** a domain entity class inherits from `Entity` with `table=True`
- **THEN** instances have `id`, `created_at`, and `updated_at` attributes populated automatically on creation

#### Scenario: Alembic autogenerate detects no schema drift after Entity refactor
- **WHEN** `alembic revision --autogenerate` is run after all entities inherit from `Entity`
- **THEN** the generated migration file contains no `upgrade()` or `downgrade()` operations (empty migration)

#### Scenario: DTO classes are unaffected by Entity base
- **WHEN** a DTO class (e.g., `BookCreate`, `BookPublic`) is instantiated
- **THEN** it does NOT inherit `id`, `created_at`, or `updated_at` from `Entity` (DTOs remain plain `SQLModel` subclasses)

### Requirement: Shared SortOrder enum in core.sorting
The system SHALL provide a `SortOrder(StrEnum)` enum in `src/app/core/sorting.py` with values `asc` and `desc`. All slice domain model files SHALL NOT define their own `SortOrder` enum. All consumers that need `SortOrder` (routers, SQL repositories, fake repositories, tests) SHALL import it directly from `app.core.sorting`.

#### Scenario: SortOrder values are usable from any slice
- **WHEN** any slice router or service references `SortOrder.asc` or `SortOrder.desc`
- **THEN** the value resolves correctly from the shared import

### Requirement: is_constraint_violated utility for IntegrityError checks
The system SHALL provide an `is_constraint_violated(exc: IntegrityError, constraint_name: str) -> bool` function in `src/app/core/db.py`. SQL repository classes SHALL use this function instead of per-repository private `_is_xxx_conflict()` helpers.

#### Scenario: Named constraint collision is detected
- **WHEN** `is_constraint_violated(exc, "uq_books_isbn")` is called with an `IntegrityError` whose `orig` message contains `"uq_books_isbn"`
- **THEN** the function returns `True`

#### Scenario: Unrelated IntegrityError is not misidentified
- **WHEN** `is_constraint_violated(exc, "uq_books_isbn")` is called with an `IntegrityError` whose `orig` message does NOT contain `"uq_books_isbn"`
- **THEN** the function returns `False`

### Requirement: PaginatedResponse generic base for list envelopes
The system SHALL provide a `PaginatedResponse[T]` generic class in `src/app/core/pagination.py` that declares `items: list[T]`, `total: int`, `page: int`, `size: int`, and a `pages` computed field (`ceil(total / size) if total > 0 else 0`). Each slice SHALL define a concrete named subclass (e.g., `class BookListResponse(PaginatedResponse[BookPublic]): pass`) to preserve OpenAPI component names.

#### Scenario: pages computed field is correct for non-empty result
- **WHEN** a `PaginatedResponse` subclass is constructed with `total=25`, `page=1`, `size=10`
- **THEN** `pages` equals `3`

#### Scenario: pages computed field is zero for empty result
- **WHEN** a `PaginatedResponse` subclass is constructed with `total=0`, `page=1`, `size=20`
- **THEN** `pages` equals `0`

#### Scenario: OpenAPI schema uses concrete subclass name
- **WHEN** a router declares `response_model=BookListResponse`
- **THEN** the OpenAPI spec contains a component named `BookListResponse`, not `PaginatedResponse_BookPublic_`

### Requirement: core module has no imports from any slice
The `src/app/core/` module SHALL NOT import from any slice package (`app.books`, `app.members`, `app.book_copies`, `app.loans`). The dependency direction is strictly slices → core.

#### Scenario: core module files import only from stdlib and third-party packages
- **WHEN** any file in `src/app/core/` is inspected
- **THEN** it contains no import statements referencing `app.books`, `app.members`, `app.book_copies`, or `app.loans`

### Requirement: Canonical fake repositories shared across service tests
The system SHALL provide canonical in-memory fake repository implementations in `tests/fakes/`, one file per slice domain. Each fake SHALL implement the full repository interface (no stubs, no `# pragma: no cover` methods), SHALL include an `add()` helper for seeding test data, and SHALL be importable by any test file. `FakeBookRepository` SHALL additionally expose `set_copies(book_id, n)` for simulating copy counts.

#### Scenario: Fake repository used in cross-slice service test
- **WHEN** `test_loan_service.py` needs a `FakeMemberRepository`
- **THEN** it imports it from `tests/fakes/member_fakes.py` and does NOT define its own local version

#### Scenario: All fake methods are exercised without pragma coverage exclusions
- **WHEN** the full test suite runs
- **THEN** no method in `tests/fakes/` requires `# pragma: no cover`

### Requirement: alembic/env.py registers all domain models
`alembic/env.py` SHALL import all domain model modules so that `SQLModel.metadata` contains every table before autogenerate runs. This includes `app.loans.domain.loan_model`, which was previously missing.

#### Scenario: autogenerate sees the loans table
- **WHEN** `alembic revision --autogenerate` is run with an up-to-date database
- **THEN** the migration does NOT contain any operation on the `loans` table
