## MODIFIED Requirements

### Requirement: BookPublic exposes copies_total

The `BookPublic` schema SHALL include a `copies_total: int` field representing the number of `BookCopy` records that reference this `Book`, and a `copies_available: int` field representing the number of those copies that are not currently on an active loan.

Both values SHALL be derived at query time — no denormalized columns on the `books` table:
- `copies_total`: count of `BookCopy` rows where `book_id` matches (unchanged from previous definition).
- `copies_available`: count of `BookCopy` rows where `book_id` matches AND no active `Loan` exists for that copy (`returned_at IS NULL` means the copy is on loan; copies without any loan row or with only returned loans are available).

Both values SHALL be computed via a single aggregated SQL statement (correlated subquery or `LEFT JOIN ... GROUP BY`) — no per-book follow-up queries, no N+1.

Both fields SHALL be exposed by `GET /books` (every item in `BookListResponse.items`) and `GET /books/{book_id}`.

The `copies_available` computation in `sql_book_repository.py` SHALL use `col(Loan.book_copy_id)` and `col(Loan.returned_at)` via a direct import of `Loan` from `app.loans.domain.loan_model`. Infrastructure-to-infrastructure cross-slice imports are acceptable; the constraint is that domain layers do not import from other slices.

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
- **AND** the response body has `copies_available` equal to `0`

#### Scenario: copies_total is calculated without N+1

- **WHEN** the application handles `GET /books` against a database with N books and M copies
- **THEN** the total number of SQL queries executed to populate the response is bounded (does not grow linearly with N)

#### Scenario: copies_available reflects active loans

- **WHEN** a book has 3 copies and 2 of them are currently on active (or overdue) loans
- **THEN** `GET /books/{book_id}` returns `copies_total = 3` and `copies_available = 1`

#### Scenario: copies_available treats returned loans as available

- **WHEN** a book copy had a past loan that was returned
- **THEN** that copy is counted in `copies_available`

#### Scenario: copies_available is calculated without N+1

- **WHEN** the application handles `GET /books` against a database with N books, M copies, and L active loans
- **THEN** the total number of SQL queries executed to populate the response is bounded (does not grow linearly with N)
