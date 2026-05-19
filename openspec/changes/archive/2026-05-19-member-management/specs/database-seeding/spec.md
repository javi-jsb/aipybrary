# Database Seeding

## Purpose

Provide a standalone script that populates the database with example book and member records for development and manual testing. The script runs on demand, outside the API's normal operation.

## ADDED Requirements

### Requirement: Seed script populates example members

The `scripts/seed.py` script SHALL also insert a predefined set of example members into the database, reusing the application's database module and `Member` model — it SHALL NOT define its own database connection logic.

The seed dataset SHALL contain at least 10 members with the following coverage:
- A mix of `status` values: at least 8 `active` and at least 2 `suspended`, so that filtering/sorting by status is non-trivial.
- Unique `email` values (the `members` table enforces a unique constraint on `email`).

#### Scenario: Seed members on empty database

- **WHEN** a developer runs `uv run python scripts/seed.py` against an empty database (with migrations applied)
- **THEN** the database contains at least 10 example members

### Requirement: Seeding is idempotent per entity

The seed script SHALL decide independently, per entity type, whether to insert records: it seeds books only if no books exist, and seeds members only if no members exist. Seeding one entity type SHALL NOT be skipped because the other already has data.

#### Scenario: Members seeded when books already present

- **WHEN** a developer runs `uv run python scripts/seed.py` against a database that already contains books but no members
- **THEN** the example members are inserted
- **AND** no duplicate books are created

#### Scenario: Seed is idempotent for members

- **WHEN** a developer runs `uv run python scripts/seed.py` twice
- **THEN** the second run does not create duplicate member records
