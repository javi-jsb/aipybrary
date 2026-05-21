# Lending

## Purpose

Provide the borrow/return lifecycle for the library — the `Loan` entity that links a member to a book copy for a fixed period. This includes the domain model, repository abstraction, application service, loan policy settings, HTTP endpoints, and the database migration for the loans table.

## Requirements

### Requirement: Loan domain model

The application SHALL define a `Loan` entity as a SQLModel table class with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | PK, default UUIDv7 via `uuid_utils.uuid7()` |
| `member_id` | `uuid.UUID` | FK `members.id` ON DELETE RESTRICT, NOT NULL |
| `book_copy_id` | `uuid.UUID` | FK `book_copies.id` ON DELETE RESTRICT, NOT NULL |
| `due_date` | `datetime` | NOT NULL, computed at borrow time as `created_at + loan_period_days` |
| `returned_at` | `datetime \| None` | NULL = active or overdue; set to `now()` on return |
| `created_at` | `datetime` | Server-default `now()`, not client-updatable — semantically the borrow timestamp |
| `updated_at` | `datetime` | Server-default `now()`, auto-updated on modification |

`LoanStatus` SHALL be a `StrEnum` with members `active`, `overdue`, and `returned`. It is derived at read time — NOT stored as a column:

- `returned`: `returned_at IS NOT NULL`
- `overdue`: `returned_at IS NULL AND due_date < now()`
- `active`: `returned_at IS NULL AND due_date >= now()`

The domain SHALL define the following Pydantic schemas:
- `LoanCreate`: fields `member_id: uuid.UUID` and `book_copy_id: uuid.UUID` only. The client does not supply `due_date`.
- `LoanPublic`: fields `id`, `member_id`, `book_copy_id`, `due_date`, `returned_at`, `created_at`, `updated_at`, and a `@computed_field` `status: LoanStatus`.
- `LoanListResponse`: paginated envelope with `items: list[LoanPublic]`, `total: int`, `page: int`, `size: int`, and a computed `pages: int`.

#### Scenario: Loan is created with required fields

- **WHEN** a Loan is instantiated with `member_id`, `book_copy_id`, and `due_date`
- **THEN** it receives a UUIDv7 `id`, `created_at` and `updated_at` are set automatically, and `returned_at` is `None`

#### Scenario: LoanStatus is active for non-returned loan with future due date

- **WHEN** a `LoanPublic` is constructed from a Loan with `returned_at = None` and `due_date` in the future
- **THEN** its `status` is `active`

#### Scenario: LoanStatus is overdue for non-returned loan past due date

- **WHEN** a `LoanPublic` is constructed from a Loan with `returned_at = None` and `due_date` in the past
- **THEN** its `status` is `overdue`

#### Scenario: LoanStatus is returned when returned_at is set

- **WHEN** a `LoanPublic` is constructed from a Loan with `returned_at` set to a datetime value
- **THEN** its `status` is `returned` regardless of `due_date`

### Requirement: Loan repository abstraction

The domain SHALL define a `LoanRepository` ABC that declares the contract for loan persistence operations: `create`, `get_by_id`, `get_filtered`, `mark_returned`, `undo_return`, `delete`, `count_active_for_member`, `get_active_for_copy`.

The infrastructure layer SHALL provide `SqlModelLoanRepository` that inherits from `LoanRepository` and implements all methods using SQLModel async sessions.

#### Scenario: Repository contract is enforced

- **WHEN** a class inherits from `LoanRepository` but does not implement all abstract methods
- **THEN** Python raises `TypeError` at instantiation time

### Requirement: Loan application service

The application layer SHALL provide a `LoanService` that receives a `LoanRepository`, a `MemberRepository`, and a `BookCopyRepository` via constructor injection and orchestrates the loan lifecycle.

The service MUST NOT depend on SQLModel, FastAPI, or any infrastructure detail — only on the domain ABCs and models.

The service SHALL enforce the following invariants in the borrow operation, in this order:
1. `member_id` references an existing member → raises `MemberNotFoundError` if not
2. Member `status` is `active` → raises `MemberSuspendedError` if suspended
3. `book_copy_id` references an existing book copy → raises `BookCopyNotFoundError` if not
4. The book copy has no active loan → raises `BookCopyNotAvailableError` if already lent
5. The member has fewer than `loan_max_active` active loans → raises `LoanLimitExceededError` if at limit

`due_date` SHALL be computed by the service as `now() + timedelta(days=settings.loan_period_days)`. The client does not supply it.

#### Scenario: Service borrows a book successfully

- **WHEN** `LoanService.borrow(member_id, book_copy_id)` is called with a valid active member and an available copy
- **AND** the member has fewer active loans than the configured limit
- **THEN** a new Loan is created and returned with `returned_at = None` and a `due_date` set to `now() + loan_period_days`

#### Scenario: Service raises MemberNotFoundError for unknown member

- **WHEN** `LoanService.borrow(member_id, book_copy_id)` is called with a `member_id` that does not exist
- **THEN** `MemberNotFoundError` is raised

#### Scenario: Service raises MemberSuspendedError for suspended member

- **WHEN** `LoanService.borrow(member_id, book_copy_id)` is called with a member whose `status` is `suspended`
- **THEN** `MemberSuspendedError` is raised

#### Scenario: Service raises BookCopyNotFoundError for unknown copy

- **WHEN** `LoanService.borrow(member_id, book_copy_id)` is called with a `book_copy_id` that does not exist
- **THEN** `BookCopyNotFoundError` is raised

#### Scenario: Service raises BookCopyNotAvailableError when copy is already on loan

- **WHEN** `LoanService.borrow(member_id, book_copy_id)` is called with a copy that already has an active loan
- **THEN** `BookCopyNotAvailableError` is raised

#### Scenario: Service raises LoanLimitExceededError when member is at active loan limit

- **WHEN** `LoanService.borrow(member_id, book_copy_id)` is called for a member who already has `loan_max_active` active loans
- **THEN** `LoanLimitExceededError` is raised

### Requirement: Loan policy settings

The application SHALL expose two configurable loan policy values via Pydantic Settings in `config.py`, overridable by environment variable:

- `LOAN_PERIOD_DAYS` (default: `14`): number of days from borrow date to `due_date`.
- `LOAN_MAX_ACTIVE` (default: `3`): maximum number of concurrently active loans per member.

#### Scenario: Default loan period is 14 days

- **WHEN** no `LOAN_PERIOD_DAYS` environment variable is set
- **AND** a loan is created
- **THEN** `due_date` is equal to `created_at + 14 days`

#### Scenario: Loan period is configurable

- **WHEN** `LOAN_PERIOD_DAYS` is set to `7`
- **AND** a loan is created
- **THEN** `due_date` is equal to `created_at + 7 days`

### Requirement: Borrow a book copy

The API SHALL expose `POST /loans` that creates a new loan from a `LoanCreate` payload (`member_id`, `book_copy_id`).

| Condition | HTTP status |
|---|---|
| Success | `201 Created` |
| `member_id` not found | `404 Not Found` |
| Member is suspended | `422 Unprocessable Content` |
| `book_copy_id` not found | `404 Not Found` |
| Book copy already on loan | `409 Conflict` |
| Member at active loan limit | `422 Unprocessable Content` |

#### Scenario: Valid borrow

- **WHEN** a client sends `POST /loans` with a valid `member_id` (active member) and `book_copy_id` (available copy)
- **AND** the member has fewer active loans than the limit
- **THEN** the response status code is `201`
- **AND** the response body is a `LoanPublic` with `returned_at = null` and `status = active`

#### Scenario: Member not found

- **WHEN** a client sends `POST /loans` with a `member_id` that does not exist
- **THEN** the response status code is `404`

#### Scenario: Member is suspended

- **WHEN** a client sends `POST /loans` with a `member_id` referencing a suspended member
- **THEN** the response status code is `422`

#### Scenario: Book copy not found

- **WHEN** a client sends `POST /loans` with a `book_copy_id` that does not exist
- **THEN** the response status code is `404`

#### Scenario: Book copy already on loan

- **WHEN** a client sends `POST /loans` with a `book_copy_id` that has an active loan
- **THEN** the response status code is `409`

#### Scenario: Member at active loan limit

- **WHEN** a client sends `POST /loans` for a member who already has `loan_max_active` active loans
- **THEN** the response status code is `422`

### Requirement: Return a book copy

The API SHALL expose `POST /loans/{loan_id}/return` that marks a loan as returned by setting `returned_at = now()`.

| Condition | HTTP status |
|---|---|
| Success | `200 OK` |
| Loan not found | `404 Not Found` |
| Loan already returned | `409 Conflict` |

#### Scenario: Valid return

- **WHEN** a client sends `POST /loans/{loan_id}/return` for an active or overdue loan
- **THEN** the response status code is `200`
- **AND** the response body is the updated `LoanPublic` with `returned_at` set to a non-null timestamp
- **AND** `status` is `returned`

#### Scenario: Loan not found

- **WHEN** a client sends `POST /loans/{loan_id}/return` with a non-existent `loan_id`
- **THEN** the response status code is `404`

#### Scenario: Loan already returned

- **WHEN** a client sends `POST /loans/{loan_id}/return` for a loan whose `returned_at` is already set
- **THEN** the response status code is `409`

### Requirement: Undo a mistaken return

The API SHALL expose `DELETE /loans/{loan_id}/return` that undoes a return by setting `returned_at` back to `None`. This is the correction path for a librarian who marked a loan returned by mistake.

The endpoint SHALL only succeed if `returned_at IS NOT NULL`. It SHALL verify that the book copy has no other active loan after the undo (guard against data races).

| Condition | HTTP status |
|---|---|
| Success | `200 OK` |
| Loan not found | `404 Not Found` |
| Loan is not returned | `409 Conflict` |

#### Scenario: Valid undo return

- **WHEN** a client sends `DELETE /loans/{loan_id}/return` for a loan whose `returned_at` is set
- **THEN** the response status code is `200`
- **AND** the response body is the updated `LoanPublic` with `returned_at = null`
- **AND** `status` is `active` or `overdue` depending on `due_date`
- **AND** `updated_at` reflects the time of this modification

#### Scenario: Loan not found

- **WHEN** a client sends `DELETE /loans/{loan_id}/return` with a non-existent `loan_id`
- **THEN** the response status code is `404`

#### Scenario: Loan is not returned

- **WHEN** a client sends `DELETE /loans/{loan_id}/return` for a loan whose `returned_at` is `None`
- **THEN** the response status code is `409`

### Requirement: Cancel an active loan

The API SHALL expose `DELETE /loans/{loan_id}` that permanently removes an active loan. This is the correction path for a loan created by mistake. The endpoint SHALL only succeed if `returned_at IS NULL` (loan is active or overdue).

| Condition | HTTP status |
|---|---|
| Success | `204 No Content` |
| Loan not found | `404 Not Found` |
| Loan is already returned | `409 Conflict` |

#### Scenario: Valid cancellation

- **WHEN** a client sends `DELETE /loans/{loan_id}` for a loan whose `returned_at` is `None`
- **THEN** the response status code is `204`
- **AND** the loan is no longer retrievable via `GET /loans/{loan_id}`

#### Scenario: Loan not found

- **WHEN** a client sends `DELETE /loans/{loan_id}` with a non-existent `loan_id`
- **THEN** the response status code is `404`

#### Scenario: Cannot cancel a returned loan

- **WHEN** a client sends `DELETE /loans/{loan_id}` for a loan whose `returned_at` is set
- **THEN** the response status code is `409`
- **AND** the loan record is not deleted

### Requirement: Get a loan by ID

The API SHALL expose `GET /loans/{loan_id}` that returns a single `LoanPublic`.

#### Scenario: Loan exists

- **WHEN** a client sends `GET /loans/{loan_id}` with a valid existing ID
- **THEN** the response status code is `200`
- **AND** the response body is a `LoanPublic` with the correct `status` derived field

#### Scenario: Loan does not exist

- **WHEN** a client sends `GET /loans/{loan_id}` with a non-existent ID
- **THEN** the response status code is `404`

### Requirement: List loans

The API SHALL expose `GET /loans` that returns a paginated `LoanListResponse` with filtering and sorting.

**Filters (all optional, AND-combined):**
- `member_id: uuid.UUID` — exact match
- `book_copy_id: uuid.UUID` — exact match
- `status: LoanStatus` — derived filter applied in SQL: `active`, `overdue`, or `returned`

**Sort:** `sort_by` ∈ `created_at` / `due_date` / `returned_at`; `order` ∈ `asc` / `desc`. Default: `created_at` / `desc`.

**Pagination:** `page` (default `1`, min `1`), `size` (default `20`, min `1`, max `100`).

The `status` filter SHALL be implemented as a SQL predicate — not as post-query filtering. Specifically:
- `active`: `returned_at IS NULL AND due_date >= now()`
- `overdue`: `returned_at IS NULL AND due_date < now()`
- `returned`: `returned_at IS NOT NULL`

#### Scenario: List all loans with default pagination

- **WHEN** a client sends `GET /loans` with no query parameters
- **THEN** the response status code is `200`
- **AND** the response body is a `LoanListResponse` with `page = 1`, `size = 20`

#### Scenario: Filter by member_id

- **WHEN** a client sends `GET /loans?member_id=<uuid>` for a member with 2 loans
- **THEN** only those 2 loans are returned

#### Scenario: Filter by status active

- **WHEN** a client sends `GET /loans?status=active`
- **THEN** only loans with `returned_at IS NULL AND due_date >= now()` are returned

#### Scenario: Filter by status overdue

- **WHEN** a client sends `GET /loans?status=overdue`
- **THEN** only loans with `returned_at IS NULL AND due_date < now()` are returned

#### Scenario: Filter by status returned

- **WHEN** a client sends `GET /loans?status=returned`
- **THEN** only loans with `returned_at IS NOT NULL` are returned

#### Scenario: Sort by due_date ascending

- **WHEN** a client sends `GET /loans?sort_by=due_date&order=asc`
- **THEN** the response `items` are ordered by `due_date` ascending

### Requirement: Loans Alembic migration

The `loans` table SHALL be created and managed via Alembic migration, not via `SQLModel.metadata.create_all()`.

The migration SHALL create the `loans` table with:
- `member_id` FK to `members.id` with `ON DELETE RESTRICT`, named `fk_loans_member_id_members`
- `book_copy_id` FK to `book_copies.id` with `ON DELETE RESTRICT`, named `fk_loans_book_copy_id_book_copies`
- Index on `member_id` and `book_copy_id` for query performance

The migration SHALL be reversible: `downgrade` drops the `loans` table.

#### Scenario: Migration creates the table

- **WHEN** a developer runs `alembic upgrade head` on a database without the `loans` table
- **THEN** the `loans` table exists with all columns and constraints matching the `Loan` model

#### Scenario: Migration is reversible

- **WHEN** a developer runs `alembic downgrade -1` after applying the loans migration
- **THEN** the `loans` table is dropped
- **AND** re-applying the migration recreates it

#### Scenario: FK RESTRICT blocks member deletion with loan history

- **WHEN** a developer attempts to delete a `Member` record that has at least one associated `Loan`
- **THEN** the database rejects the operation with a foreign key constraint error

#### Scenario: FK RESTRICT blocks book copy deletion with loan history

- **WHEN** a developer attempts to delete a `BookCopy` record that has at least one associated `Loan`
- **THEN** the database rejects the operation with a foreign key constraint error

