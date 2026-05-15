# Book Management

## Purpose

Provide CRUD operations for the Book entity — the core domain object of the library API. This includes the domain model, repository abstraction, application service, HTTP endpoints, and the database migration for the books table.

## ADDED Requirements

### Requirement: Book domain model

The application SHALL define a `Book` entity as a SQLModel table class with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | PK, default UUIDv7 via `uuid_utils.uuid7()` |
| `title` | `str` | Required, max 500 chars |
| `author` | `str` | Required, max 300 chars |
| `isbn` | `str \| None` | Optional, max 13 chars, unique when present |
| `publication_year` | `int \| None` | Optional |
| `created_at` | `datetime` | Server-default `now()`, not client-updatable |
| `updated_at` | `datetime` | Server-default `now()`, auto-updated on modification |

The model SHALL also define separate Pydantic schemas for API boundaries: `BookCreate`, `BookUpdate`, and `BookPublic`.

#### Scenario: Book is created with all required fields

- **WHEN** a Book is instantiated with `title` and `author`
- **THEN** it receives a UUIDv7 `id`, `created_at`, and `updated_at` are set automatically

#### Scenario: ISBN uniqueness is enforced

- **WHEN** two books are created with the same non-null `isbn`
- **THEN** the database rejects the second insert with a unique constraint violation

#### Scenario: Multiple books without ISBN are allowed

- **WHEN** two books are created with `isbn` set to `None`
- **THEN** both are stored successfully (NULL is not considered a duplicate)

### Requirement: Book repository abstraction

The domain SHALL define a `BookRepository` ABC that declares the contract for book persistence operations: `create`, `get_by_id`, `get_all`, `update`, `delete`.

The infrastructure layer SHALL provide `SqlModelBookRepository` that inherits from `BookRepository` and implements all methods using SQLModel async sessions.

#### Scenario: Repository contract is enforced

- **WHEN** a class inherits from `BookRepository` but does not implement all abstract methods
- **THEN** Python raises `TypeError` at instantiation time

### Requirement: Book application service

The application layer SHALL provide a `BookService` that receives a `BookRepository` via constructor injection and orchestrates CRUD operations.

The service MUST NOT depend on SQLModel, FastAPI, or any infrastructure detail — only on the domain's `BookRepository` ABC and model.

#### Scenario: Service creates a book

- **WHEN** `BookService.create(data)` is called with valid `BookCreate` data
- **THEN** it delegates to the repository and returns the created `Book`

#### Scenario: Service returns None for missing book

- **WHEN** `BookService.get_by_id(id)` is called with a non-existent ID
- **THEN** it returns `None`

### Requirement: List all books

The API SHALL expose `GET /books` that returns all books in the database.

#### Scenario: Books exist

- **WHEN** a client sends `GET /books`
- **AND** the database contains books
- **THEN** the response status code is `200`
- **AND** the response body is a JSON array of `BookPublic` objects

#### Scenario: No books exist

- **WHEN** a client sends `GET /books`
- **AND** the database is empty
- **THEN** the response status code is `200`
- **AND** the response body is an empty JSON array `[]`

### Requirement: Get a book by ID

The API SHALL expose `GET /books/{book_id}` that returns a single book.

#### Scenario: Book exists

- **WHEN** a client sends `GET /books/{book_id}` with a valid existing ID
- **THEN** the response status code is `200`
- **AND** the response body is a JSON `BookPublic` object

#### Scenario: Book does not exist

- **WHEN** a client sends `GET /books/{book_id}` with a non-existent ID
- **THEN** the response status code is `404`

### Requirement: Create a book

The API SHALL expose `POST /books` that creates a new book from a `BookCreate` payload.

#### Scenario: Valid creation

- **WHEN** a client sends `POST /books` with a valid JSON body containing `title` and `author`
- **THEN** the response status code is `201`
- **AND** the response body is the created `BookPublic` object with a generated `id`

#### Scenario: Missing required fields

- **WHEN** a client sends `POST /books` without `title` or `author`
- **THEN** the response status code is `422` with validation error details

### Requirement: Update a book

The API SHALL expose `PATCH /books/{book_id}` that partially updates an existing book from a `BookUpdate` payload.

#### Scenario: Valid partial update

- **WHEN** a client sends `PATCH /books/{book_id}` with a subset of fields
- **THEN** the response status code is `200`
- **AND** only the provided fields are updated; other fields remain unchanged
- **AND** the response body is the updated `BookPublic` object

#### Scenario: Book does not exist

- **WHEN** a client sends `PATCH /books/{book_id}` with a non-existent ID
- **THEN** the response status code is `404`

### Requirement: Delete a book

The API SHALL expose `DELETE /books/{book_id}` that removes a book.

#### Scenario: Book exists

- **WHEN** a client sends `DELETE /books/{book_id}` with a valid existing ID
- **THEN** the response status code is `204`
- **AND** the book is no longer retrievable via `GET /books/{book_id}`

#### Scenario: Book does not exist

- **WHEN** a client sends `DELETE /books/{book_id}` with a non-existent ID
- **THEN** the response status code is `404`

### Requirement: Books table migration

The books table SHALL be created and managed via an Alembic migration, not via `SQLModel.metadata.create_all()`.

#### Scenario: Migration creates the table

- **WHEN** a developer runs `alembic upgrade head` on a fresh database
- **THEN** the `books` table exists with all columns matching the Book model

#### Scenario: Migration is reversible

- **WHEN** a developer runs `alembic downgrade -1` after applying the books migration
- **THEN** the `books` table is dropped
