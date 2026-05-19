## MODIFIED Requirements

### Requirement: Create a book

The API SHALL expose `POST /books` that creates a new book from a `BookCreate` payload.

A duplicate `isbn` (a value already used by another book) SHALL be rejected with HTTP `409 Conflict`, not surfaced as a `500`. Any other database integrity violation SHALL NOT be mapped to `409`.

#### Scenario: Valid creation

- **WHEN** a client sends `POST /books` with a valid JSON body containing `title` and `author`
- **THEN** the response status code is `201`
- **AND** the response body is the created `BookPublic` object with a generated `id`

#### Scenario: Missing required fields

- **WHEN** a client sends `POST /books` without `title` or `author`
- **THEN** the response status code is `422` with validation error details

#### Scenario: Duplicate ISBN rejected

- **WHEN** a client sends `POST /books` with an `isbn` that already exists
- **THEN** the response status code is `409`

### Requirement: Update a book

The API SHALL expose `PATCH /books/{book_id}` that partially updates an existing book from a `BookUpdate` payload.

Updating `isbn` to a value already used by another book SHALL be rejected with HTTP `409 Conflict`, not surfaced as a `500`. Any other database integrity violation SHALL NOT be mapped to `409`.

#### Scenario: Valid partial update

- **WHEN** a client sends `PATCH /books/{book_id}` with a subset of fields
- **THEN** the response status code is `200`
- **AND** only the provided fields are updated; other fields remain unchanged
- **AND** the response body is the updated `BookPublic` object

#### Scenario: Book does not exist

- **WHEN** a client sends `PATCH /books/{book_id}` with a non-existent ID
- **THEN** the response status code is `404`

#### Scenario: Update to a duplicate ISBN rejected

- **WHEN** a client sends `PATCH /books/{book_id}` setting `isbn` to a value already used by another book
- **THEN** the response status code is `409`

### Requirement: Books table migration

The books table SHALL be created and managed via Alembic migrations, not via `SQLModel.metadata.create_all()`.

The `isbn` unique constraint SHALL be explicitly named `uq_books_isbn` so the SQL repository can distinguish an ISBN collision from any other integrity violation. Because the books table was originally created with an unnamed unique constraint (Postgres default `books_isbn_key`), a dedicated reversible migration SHALL rename it to `uq_books_isbn`.

#### Scenario: Migration creates the table

- **WHEN** a developer runs `alembic upgrade head` on a fresh database
- **THEN** the `books` table exists with all columns matching the Book model
- **AND** the `isbn` unique constraint is named `uq_books_isbn`

#### Scenario: Constraint-rename migration is reversible

- **WHEN** a developer runs `alembic downgrade -1` after applying the ISBN-constraint-rename migration
- **THEN** the `isbn` unique constraint reverts to the unnamed default (`books_isbn_key`)
- **AND** re-applying the revision restores the `uq_books_isbn` name

#### Scenario: Books table migration is reversible

- **WHEN** a developer downgrades to before the create-books revision
- **THEN** the `books` table is dropped
