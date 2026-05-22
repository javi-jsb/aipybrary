## ADDED Requirements

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

## MODIFIED Requirements

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
