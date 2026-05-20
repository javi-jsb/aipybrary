## MODIFIED Requirements

### Requirement: Delete a book

The API SHALL expose `DELETE /books/{book_id}` that removes a book.

When the book has at least one associated `BookCopy`, deletion SHALL be refused with HTTP `409 Conflict`. This is enforced at the database level by a foreign key on `book_copies.book_id` with `ON DELETE RESTRICT`; the SQL repository SHALL catch the resulting `IntegrityError` and translate it to a domain exception (e.g., `BookHasCopiesError`) that the router maps to `409`. Any other database integrity violation SHALL NOT be mapped to `409`.

#### Scenario: Book exists

- **WHEN** a client sends `DELETE /books/{book_id}` with a valid existing ID
- **AND** the book has no associated `BookCopy` records
- **THEN** the response status code is `204`
- **AND** the book is no longer retrievable via `GET /books/{book_id}`

#### Scenario: Book does not exist

- **WHEN** a client sends `DELETE /books/{book_id}` with a non-existent ID
- **THEN** the response status code is `404`

#### Scenario: Book has copies

- **WHEN** a client sends `DELETE /books/{book_id}` for a book that has at least one associated `BookCopy`
- **THEN** the response status code is `409`
- **AND** the book remains retrievable via `GET /books/{book_id}`

## ADDED Requirements

### Requirement: BookPublic exposes copies_total

The `BookPublic` schema SHALL include a `copies_total: int` field representing the number of `BookCopy` records that reference this `Book`.

The value SHALL be derived at query time from the `book_copies` table, calculated via a single aggregated SQL statement (correlated subquery or `LEFT JOIN ... GROUP BY`) — no per-book follow-up query, no N+1.

The value SHALL be exposed by both `GET /books` (every item in `BookListResponse.items`) and `GET /books/{book_id}`. It SHALL NOT be stored as a denormalised column on the `books` table; it is computed on read.

A future capability MAY add `copies_available` to the same schema; that field is intentionally out of scope here because it depends on the `Loan` entity (Phase 3 of the lending roadmap).

#### Scenario: BookPublic returned by GET /books includes copies_total

- **WHEN** a client sends `GET /books`
- **AND** the database contains a book with 3 associated `BookCopy` records and another book with 0
- **THEN** the response status code is `200`
- **AND** the `BookPublic` object for the first book has `copies_total` equal to `3`
- **AND** the `BookPublic` object for the second book has `copies_total` equal to `0`

#### Scenario: BookPublic returned by GET /books/{book_id} includes copies_total

- **WHEN** a client sends `GET /books/{book_id}` for a book with 2 associated `BookCopy` records
- **THEN** the response status code is `200`
- **AND** the response body has `copies_total` equal to `2`

#### Scenario: Newly created book has zero copies

- **WHEN** a client sends `POST /books` with a valid payload
- **AND** then sends `GET /books/{book_id}` for the created book
- **THEN** the response body has `copies_total` equal to `0`

#### Scenario: copies_total is calculated without N+1

- **WHEN** the application handles `GET /books` against a database with N books and M copies
- **THEN** the total number of SQL queries executed to populate the response is bounded (does not grow linearly with N)
