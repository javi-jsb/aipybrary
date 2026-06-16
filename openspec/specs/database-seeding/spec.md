# Database Seeding

## Purpose

Provide a standalone script that populates the database with example book and member records for development and manual testing. The script runs on demand, outside the API's normal operation.
## Requirements
### Requirement: Seed script populates example books

The project SHALL provide a standalone Python script at `scripts/seed.py` that inserts a predefined set of example books into the database.

The script MUST import and reuse the application's database module and Book model — it SHALL NOT define its own database connection logic.

The seed dataset SHALL contain at least 20 books with the following coverage:
- Diverse genres (literary fiction, science fiction, fantasy, essay, poetry, thriller) and cultures (Latin American, European, Asian, North American, African)
- At least 3 books without an `isbn` value
- At least 3 books without a `publication_year` value
- At least 6 books without a `synopsis` value
- Publication years spanning at least 5 decades, to make sorting by year non-trivial

#### Scenario: Seed on empty database

- **WHEN** a developer runs `uv run python scripts/seed.py` against an empty database (with migrations applied)
- **THEN** the database contains at least 20 example books

#### Scenario: Seed is idempotent

- **WHEN** a developer runs `uv run python scripts/seed.py` twice
- **THEN** the second run does not create duplicate records

### Requirement: Seed script is independent of the API

The seed script MUST NOT require the FastAPI application to be running. It connects directly to the database using the same configuration as the application.

#### Scenario: API is not running

- **WHEN** a developer runs `uv run python scripts/seed.py` while the FastAPI server is stopped
- **THEN** the script completes successfully

### Requirement: Seed script populates example users

The `scripts/seed.py` script SHALL insert a predefined set of example users, reusing the application's database module and `User` model — it SHALL NOT define its own database connection logic.

The seed dataset SHALL include:

- Exactly one `admin` user — the bootstrap account, since with every endpoint gated no admin can be created through the API.
- At least two `staff` users.

(The `member`-role users are created together with their members in the members block.) Every seeded user SHALL have a hashed password — never stored in plaintext — and `is_active` `true`. The seeded admin's credentials SHALL be known to the developer (fixed dev defaults or environment-provided) so the bootstrap account can be used to log in.

#### Scenario: Seed users on empty database

- **WHEN** a developer runs `uv run python scripts/seed.py` against an empty database (with migrations applied)
- **THEN** the database contains exactly one `admin` user and at least two `staff` users

#### Scenario: Seeded admin can authenticate

- **WHEN** the seed has run
- **AND** a client sends `POST /auth/login` with the seeded admin credentials
- **THEN** the response status code is `200` and the body contains an access token

#### Scenario: Seed is idempotent for users

- **WHEN** a developer runs `uv run python scripts/seed.py` twice
- **THEN** the second run does not create duplicate user records

### Requirement: Seed script populates example members

The `scripts/seed.py` script SHALL insert a predefined set of example members into the database, reusing the application's database module and the `Member` and `User` models — it SHALL NOT define its own database connection logic.

Each seeded member SHALL be created together with, and linked 1:1 to, a seeded `member`-role `User` that carries the member's `email` and a hashed password.

The seed dataset SHALL contain at least 10 members with the following coverage:

- A mix of `status` values: at least 8 `active` and at least 2 `suspended`, so that filtering/sorting by status is non-trivial.
- Unique `email` values on the linked users (the `users` table enforces a unique constraint on `email`).

#### Scenario: Seed members on empty database

- **WHEN** a developer runs `uv run python scripts/seed.py` against an empty database (with migrations applied)
- **THEN** the database contains at least 10 example members
- **AND** each member is linked to a `member`-role user carrying its email

#### Scenario: Seed is idempotent for members

- **WHEN** a developer runs `uv run python scripts/seed.py` twice
- **THEN** the second run does not create duplicate member or member-user records

### Requirement: Seeding is idempotent per entity

The seed script SHALL decide independently, per entity type, whether to insert records: it seeds the `admin`/`staff` users only if no users exist, books only if no books exist, members (with their linked `member`-role users) only if no members exist, book copies only if no book copies exist, and loans only if no loans exist. Seeding one entity type SHALL NOT be skipped because another already has data.

The seeding order SHALL be: users → books → members → book copies → loans. The `admin`/`staff` users come first; members are created with their linked users in the members block; book copies depend on book IDs and loans depend on both member and book copy IDs.

#### Scenario: Members seeded when books already present

- **WHEN** a developer runs `uv run python scripts/seed.py` against a database that already contains books but no members
- **THEN** the example members and their linked member-users are inserted
- **AND** no duplicate books are created

#### Scenario: Book copies seeded when books and members already present

- **WHEN** a developer runs `uv run python scripts/seed.py` against a database that already contains books and members but no book copies
- **THEN** the example book copies are inserted
- **AND** no duplicate books or members are created

#### Scenario: Loans seeded when book copies already present

- **WHEN** a developer runs `uv run python scripts/seed.py` against a database that already contains books, members, and book copies but no loans
- **THEN** the example loans are inserted
- **AND** no duplicate book copies are created

#### Scenario: Seed is idempotent across entities

- **WHEN** a developer runs `uv run python scripts/seed.py` twice
- **THEN** the second run does not create duplicate records of any entity type

### Requirement: Seed script populates example book copies

The `scripts/seed.py` script SHALL insert a predefined set of example `BookCopy` records into the database, reusing the application's database module and `BookCopy` model.

The seed dataset SHALL contain at least 5 book copies distributed across at least 3 different books, with at least 1 copy per selected book. Each copy SHALL have a unique `barcode`.

The block SHALL be idempotent: if any `BookCopy` records exist in the database, the block is skipped entirely.

The book copies block SHALL run after the books block, since copies depend on book IDs.

#### Scenario: Seed book copies on empty database

- **WHEN** a developer runs `uv run python scripts/seed.py` against a database with books and members but no book copies
- **THEN** the database contains at least 5 example book copies

#### Scenario: Seed is idempotent for book copies

- **WHEN** a developer runs `uv run python scripts/seed.py` twice
- **THEN** the second run does not create duplicate book copy records

### Requirement: Seed script populates example loans

The `scripts/seed.py` script SHALL insert a predefined set of example `Loan` records into the database, reusing the application's database module and `Loan` model.

The seed dataset SHALL cover all three derived loan states:
- At least 1 loan with `returned_at = None` and `due_date` in the future (`status = active`)
- At least 1 loan with `returned_at = None` and `due_date` in the past (`status = overdue`)
- At least 1 loan with `returned_at` set to a past datetime (`status = returned`)

The block SHALL be idempotent: if any `Loan` records exist in the database, the block is skipped entirely.

The loans block SHALL run last (after books, members, and book copies), since loans depend on both member and book copy IDs.

#### Scenario: Seed loans on empty database

- **WHEN** a developer runs `uv run python scripts/seed.py` against a database with books, members, and book copies but no loans
- **THEN** the database contains at least 3 example loans covering all three derived states

#### Scenario: Seed is idempotent for loans

- **WHEN** a developer runs `uv run python scripts/seed.py` twice
- **THEN** the second run does not create duplicate loan records

#### Scenario: Seeded loans cover all status states

- **WHEN** a developer runs `uv run python scripts/seed.py` and then queries `GET /loans?status=active`
- **THEN** at least 1 loan is returned
- **WHEN** querying `GET /loans?status=overdue`
- **THEN** at least 1 loan is returned
- **WHEN** querying `GET /loans?status=returned`
- **THEN** at least 1 loan is returned

