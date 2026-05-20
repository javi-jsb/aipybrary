# Book Copy Management

## Purpose

Provide CRUD operations for the BookCopy entity — a physical copy of a book held by the library. This includes the domain model, repository abstraction, application service, HTTP endpoints, and the database migration for the book_copies table.

## Requirements

### Requirement: BookCopy domain model

The application SHALL define a `BookCopy` entity as a SQLModel table class with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | PK, default UUIDv7 via `uuid_utils.uuid7()` |
| `book_id` | `uuid.UUID` | Required, foreign key to `books.id` with `ON DELETE RESTRICT` |
| `barcode` | `str` | Required, max 100 chars, unique (constraint `uq_book_copies_barcode`), free format |
| `location` | `str \| None` | Optional, max 200 chars |
| `notes` | `str \| None` | Optional, no length cap, stored as TEXT |
| `created_at` | `datetime` | Server-default `now()`, not client-updatable |
| `updated_at` | `datetime` | Server-default `now()`, auto-updated on modification |

The `BookCopy` domain entity SHALL reference `Book` only by `book_id: UUID`. It MUST NOT import the `Book` model from the `books` slice.

The model SHALL define separate Pydantic schemas for API boundaries: `BookCopyCreate`, `BookCopyUpdate`, and `BookCopyPublic`, plus a `BookCopyListResponse` paginated envelope consistent with `MemberListResponse` and `BookListResponse` (`items`, `total`, `page`, `size`, and a computed `pages`).

`BookCopyUpdate` SHALL NOT include `book_id`. A copy cannot be reassigned to a different book; that operation requires delete + create.

#### Scenario: BookCopy is created with required fields

- **WHEN** a `BookCopy` is instantiated with `book_id` and `barcode`
- **THEN** it receives a UUIDv7 `id`, and `created_at` and `updated_at` are set automatically

#### Scenario: barcode uniqueness is enforced

- **WHEN** two book copies are created with the same `barcode`
- **THEN** the database rejects the second insert with a unique constraint violation

#### Scenario: book_id referential integrity is enforced

- **WHEN** a `BookCopy` is created with a `book_id` that does not exist in the `books` table
- **THEN** the database rejects the insert with a foreign key violation

#### Scenario: book deletion is restricted while copies exist

- **WHEN** the database is asked to delete a `Book` that has at least one `BookCopy`
- **THEN** the database raises a foreign key violation (`ON DELETE RESTRICT`)

### Requirement: BookCopy repository abstraction

The domain SHALL define a `BookCopyRepository` ABC that declares the contract for book-copy persistence operations: `create`, `get_by_id`, `get_paginated`, `update`, `delete`, and `count_by_book_id`.

The `count_by_book_id` method SHALL return the number of copies for a given `book_id`. It exists so that the `books` slice can compose it (or an equivalent aggregated query) to derive `copies_total` on `BookPublic`.

The infrastructure layer SHALL provide `SqlModelBookCopyRepository` that inherits from `BookCopyRepository` and implements all methods using SQLModel async sessions, mirroring `SqlModelMemberRepository` and `SqlModelBookRepository`.

#### Scenario: Repository contract is enforced

- **WHEN** a class inherits from `BookCopyRepository` but does not implement all abstract methods
- **THEN** Python raises `TypeError` at instantiation time

### Requirement: BookCopy application service

The application layer SHALL provide a `BookCopyService` that receives a `BookCopyRepository` and a `BookRepository` via constructor injection and orchestrates CRUD operations.

The `BookRepository` dependency is used exclusively to validate that `book_id` refers to an existing `Book` at creation time. The service MUST NOT depend on SQLModel, FastAPI, or any infrastructure detail — only on the domain ABCs and models of the `book_copies` and `books` slices.

#### Scenario: Service creates a copy when book exists

- **WHEN** `BookCopyService.create(data)` is called with valid `BookCopyCreate` data and a `book_id` that exists
- **THEN** it delegates to the repository and returns the created `BookCopy`

#### Scenario: Service rejects creation when book does not exist

- **WHEN** `BookCopyService.create(data)` is called with a `book_id` that does not exist in the `books` repository
- **THEN** it raises a domain exception indicating the `book_id` is invalid (without persisting)

#### Scenario: Service returns None for missing copy

- **WHEN** `BookCopyService.get_by_id(id)` is called with a non-existent ID
- **THEN** it returns `None`

### Requirement: barcode validation and uniqueness

The application SHALL surface a duplicate-barcode collision as `409 Conflict`, not as a generic database error.

The domain SHALL define a `DuplicateBarcodeError` exception. `SqlModelBookCopyRepository` SHALL catch `IntegrityError`, inspect the constraint name, and re-raise as `DuplicateBarcodeError` when the offending constraint is `uq_book_copies_barcode`. Any other integrity violation SHALL be re-raised unchanged.

`barcode` validation is free-form: required, max 100 characters, otherwise unconstrained.

#### Scenario: Duplicate barcode rejected on create

- **WHEN** a client sends `POST /book-copies` with a `barcode` that already exists
- **THEN** the response status code is `409`

#### Scenario: Duplicate barcode rejected on update

- **WHEN** a client sends `PATCH /book-copies/{copy_id}` setting `barcode` to a value already used by another copy
- **THEN** the response status code is `409`

### Requirement: Paginated book-copy list

The API SHALL expose `GET /book-copies` that returns a paginated `BookCopyListResponse` envelope (`items`, `total`, `page`, `size`, computed `pages`), mirroring the `/members` and `/books` list-query contracts.

Query parameters:

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `page` | `int` | `1` | `>= 1` |
| `size` | `int` | `20` | `>= 1`, `<= 100` |

#### Scenario: Default pagination on non-empty database

- **WHEN** a client sends `GET /book-copies` with no query parameters
- **AND** the database contains 25 copies
- **THEN** the response status code is `200`
- **AND** `items` contains 20 `BookCopyPublic` objects
- **AND** `total` is `25`, `page` is `1`, `size` is `20`, `pages` is `2`

#### Scenario: Second page

- **WHEN** a client sends `GET /book-copies?page=2&size=20`
- **AND** the database contains 25 copies
- **THEN** `items` contains 5 copies
- **AND** `page` is `2`

#### Scenario: No copies exist

- **WHEN** a client sends `GET /book-copies`
- **AND** the database is empty
- **THEN** the response status code is `200`
- **AND** `items` is `[]`, `total` is `0`, `pages` is `0`

#### Scenario: page out of range

- **WHEN** a client sends `GET /book-copies?page=0`
- **THEN** the response status code is `422`

#### Scenario: size exceeds maximum

- **WHEN** a client sends `GET /book-copies?size=101`
- **THEN** the response status code is `422`

### Requirement: Filter book copies by book_id, barcode and location

`GET /book-copies` SHALL accept optional `book_id`, `barcode`, and `location` query parameters.

| Parameter | Match type |
|---|---|
| `book_id` | Exact UUID match |
| `barcode` | Case-insensitive partial match (SQL `ILIKE`) |
| `location` | Case-insensitive partial match (SQL `ILIKE`) |

All filters are independent and additive (AND logic when more than one is provided). An invalid `book_id` value (not a valid UUID) yields `422`.

#### Scenario: Filter by book_id

- **WHEN** a client sends `GET /book-copies?book_id={uuid}` for a book with 3 copies
- **THEN** only those 3 copies are returned
- **AND** `total` is `3`

#### Scenario: Filter by barcode

- **WHEN** a client sends `GET /book-copies?barcode=ABC`
- **THEN** only copies whose `barcode` contains "ABC" (case-insensitive) are returned

#### Scenario: Filter by location

- **WHEN** a client sends `GET /book-copies?location=floor-2`
- **THEN** only copies whose `location` contains "floor-2" (case-insensitive) are returned

#### Scenario: Invalid book_id value

- **WHEN** a client sends `GET /book-copies?book_id=not-a-uuid`
- **THEN** the response status code is `422`

#### Scenario: Combined filters

- **WHEN** a client sends `GET /book-copies?book_id={uuid}&location=shelf-A`
- **THEN** only copies matching BOTH filters are returned

#### Scenario: No matches

- **WHEN** a client sends `GET /book-copies?barcode=zzznomatch`
- **THEN** the response status code is `200`
- **AND** `items` is `[]` and `total` is `0`

### Requirement: Sort book-copy list

`GET /book-copies` SHALL accept `sort_by` and `order` query parameters.

| Parameter | Allowed values | Default |
|---|---|---|
| `sort_by` | `barcode`, `location`, `created_at` | `created_at` |
| `order` | `asc`, `desc` | `desc` |

#### Scenario: Sort by barcode ascending

- **WHEN** a client sends `GET /book-copies?sort_by=barcode&order=asc`
- **THEN** the response status code is `200`
- **AND** `items` are ordered alphabetically by `barcode`

#### Scenario: Default sort

- **WHEN** a client sends `GET /book-copies` with no sort parameters
- **THEN** copies are ordered by `created_at` descending (newest first)

#### Scenario: Invalid sort_by value

- **WHEN** a client sends `GET /book-copies?sort_by=invalid`
- **THEN** the response status code is `422`

### Requirement: Get a book copy by ID

The API SHALL expose `GET /book-copies/{copy_id}` that returns a single copy.

#### Scenario: Copy exists

- **WHEN** a client sends `GET /book-copies/{copy_id}` with a valid existing ID
- **THEN** the response status code is `200`
- **AND** the response body is a JSON `BookCopyPublic` object

#### Scenario: Copy does not exist

- **WHEN** a client sends `GET /book-copies/{copy_id}` with a non-existent ID
- **THEN** the response status code is `404`

### Requirement: Create a book copy

The API SHALL expose `POST /book-copies` that creates a new copy from a `BookCopyCreate` payload. `BookCopyCreate` SHALL accept `book_id`, `barcode`, and optional `location` and `notes`.

When `book_id` does not reference an existing `Book`, the response SHALL be `422 Unprocessable Entity`, not `404` or `500`. The addressed resource (`/book-copies`) exists; the body value is semantically invalid.

A duplicate `barcode` SHALL be rejected with `409 Conflict`. Any other database integrity violation SHALL NOT be mapped to `409` or `422`.

#### Scenario: Valid creation

- **WHEN** a client sends `POST /book-copies` with a valid JSON body containing `book_id` (referring to an existing book) and `barcode`
- **THEN** the response status code is `201`
- **AND** the response body is the created `BookCopyPublic` object with a generated `id`

#### Scenario: Missing required fields

- **WHEN** a client sends `POST /book-copies` without `book_id` or `barcode`
- **THEN** the response status code is `422` with validation error details

#### Scenario: Non-existent book_id

- **WHEN** a client sends `POST /book-copies` with a `book_id` that does not exist
- **THEN** the response status code is `422`

#### Scenario: Duplicate barcode rejected

- **WHEN** a client sends `POST /book-copies` with a `barcode` that already exists
- **THEN** the response status code is `409`

### Requirement: Update a book copy

The API SHALL expose `PATCH /book-copies/{copy_id}` that partially updates an existing copy from a `BookCopyUpdate` payload. `BookCopyUpdate` SHALL allow updating `barcode`, `location`, and `notes`, each optional. `BookCopyUpdate` SHALL NOT accept `book_id` — a copy is not reassignable.

#### Scenario: Valid partial update

- **WHEN** a client sends `PATCH /book-copies/{copy_id}` with a subset of allowed fields
- **THEN** the response status code is `200`
- **AND** only the provided fields are updated; other fields remain unchanged
- **AND** the response body is the updated `BookCopyPublic` object

#### Scenario: Copy does not exist

- **WHEN** a client sends `PATCH /book-copies/{copy_id}` with a non-existent ID
- **THEN** the response status code is `404`

#### Scenario: Update to a duplicate barcode rejected

- **WHEN** a client sends `PATCH /book-copies/{copy_id}` setting `barcode` to a value already used by another copy
- **THEN** the response status code is `409`

#### Scenario: book_id is not accepted in update payload

- **WHEN** a client sends `PATCH /book-copies/{copy_id}` with a `book_id` field in the body
- **THEN** the response status code is `422` (the field is rejected by the schema)

### Requirement: Delete a book copy

The API SHALL expose `DELETE /book-copies/{copy_id}` that removes a copy.

#### Scenario: Copy exists

- **WHEN** a client sends `DELETE /book-copies/{copy_id}` with a valid existing ID
- **THEN** the response status code is `204`
- **AND** the copy is no longer retrievable via `GET /book-copies/{copy_id}`

#### Scenario: Copy does not exist

- **WHEN** a client sends `DELETE /book-copies/{copy_id}` with a non-existent ID
- **THEN** the response status code is `404`

### Requirement: Cross-slice composition at the application layer

`BookCopyService` SHALL import and depend on `BookRepository` (the ABC from `src/app/books/domain/`) via constructor injection. This cross-slice dependency is permitted at the application-service layer because the service is the orchestration point for cross-aggregate validation (book existence check before copy creation).

Domain entities and domain ports SHALL NOT cross slice boundaries. Specifically, the `BookCopy` model SHALL reference the book solely via `book_id: UUID` and SHALL NOT import any class from `src/app/books/`.

#### Scenario: BookCopy domain model is free of Book imports

- **WHEN** `src/app/book_copies/domain/book_copy_model.py` is inspected
- **THEN** it contains no import from `src/app/books/`

#### Scenario: BookCopyService validates book existence via BookRepository

- **WHEN** `BookCopyService.create(data)` runs
- **THEN** it consults `BookRepository.get_by_id(data.book_id)` before persisting
- **AND** if the book does not exist, raises a domain validation exception

### Requirement: book_copies table migration

The `book_copies` table SHALL be created and managed via an Alembic migration, not via `SQLModel.metadata.create_all()`.

The migration SHALL include:
- All columns described in the `BookCopy` domain model.
- A foreign key on `book_id` referencing `books.id` with `ON DELETE RESTRICT`.
- A unique constraint on `barcode`, explicitly named `uq_book_copies_barcode` so the SQL repository can distinguish a barcode collision from any other integrity violation.

#### Scenario: Migration creates the table

- **WHEN** a developer runs `alembic upgrade head` on a database without the `book_copies` table
- **THEN** the `book_copies` table exists with all columns matching the `BookCopy` model
- **AND** the FK on `book_id` references `books.id` with `ON DELETE RESTRICT`
- **AND** the unique constraint on `barcode` is named `uq_book_copies_barcode`

#### Scenario: Migration is reversible

- **WHEN** a developer downgrades the book_copies revision after applying it
- **THEN** the `book_copies` table is dropped
- **AND** re-applying the revision recreates it
