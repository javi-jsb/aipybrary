## ADDED Requirements

### Requirement: Book synopsis field

The `Book` entity SHALL have an optional `synopsis` field.

| Field | Type | Constraints |
|---|---|---|
| `synopsis` | `str \| None` | Optional, no length cap, stored as TEXT |

`BookCreate`, `BookUpdate`, and `BookPublic` SHALL include `synopsis` accordingly.

A new Alembic migration SHALL add the `synopsis` column (nullable, no server default) to the `books` table.

#### Scenario: Book created with synopsis

- **WHEN** a client sends `POST /books` with a `synopsis` value
- **THEN** the response status is `201`
- **AND** the returned `BookPublic` contains the provided synopsis

#### Scenario: Book created without synopsis

- **WHEN** a client sends `POST /books` without a `synopsis` field
- **THEN** the response status is `201`
- **AND** `synopsis` in the response is `null`

#### Scenario: Synopsis migration is reversible

- **WHEN** a developer runs `alembic downgrade -1` after applying the synopsis migration
- **THEN** the `synopsis` column is dropped from the `books` table

### Requirement: ISBN checksum validation

When a non-null `isbn` value is provided in `BookCreate` or `BookUpdate`, the application SHALL validate it as a well-formed ISBN-10 or ISBN-13.

Validation rules:
- Hyphens are stripped before validation and before storage
- After stripping, the value must be exactly 10 or 13 digits (ISBN-10 may end with `X`)
- ISBN-10 checksum: sum of `digit[i] * (10 - i)` for `i` in `0..8`, check digit satisfies `(sum + check) % 11 == 0` where `X` = 10
- ISBN-13 checksum: alternating weights 1 and 3, total sum must be divisible by 10

#### Scenario: Valid ISBN-13 accepted

- **WHEN** a client sends `POST /books` with `isbn` `"978-0-06-093434-7"`
- **THEN** the response status is `201`
- **AND** the stored isbn is `"9780060934347"` (hyphens stripped)

#### Scenario: Valid ISBN-10 accepted

- **WHEN** a client sends `POST /books` with `isbn` `"0-306-40615-2"`
- **THEN** the response status is `201`
- **AND** the stored isbn is `"0306406152"`

#### Scenario: Invalid checksum rejected

- **WHEN** a client sends `POST /books` with `isbn` `"9780000000000"` (invalid checksum)
- **THEN** the response status is `422`

#### Scenario: Wrong length rejected

- **WHEN** a client sends `POST /books` with `isbn` `"12345"`
- **THEN** the response status is `422`

#### Scenario: Null ISBN bypasses validation

- **WHEN** a client sends `POST /books` without an `isbn` field
- **THEN** the response status is `201`
- **AND** validation is not triggered

## MODIFIED Requirements

### Requirement: List all books

The API SHALL expose `GET /books` that returns a paginated `BookListResponse` envelope (see `book-list-query` spec) instead of a flat array.

The endpoint signature, filtering, sorting, and pagination behaviour are fully specified in the `book-list-query` capability spec.

#### Scenario: Books exist

- **WHEN** a client sends `GET /books`
- **AND** the database contains books
- **THEN** the response status code is `200`
- **AND** the response body is a `BookListResponse` with `items` containing `BookPublic` objects

#### Scenario: No books exist

- **WHEN** a client sends `GET /books`
- **AND** the database is empty
- **THEN** the response status code is `200`
- **AND** `items` is `[]`
- **AND** `total` is `0`
