# Database Seeding

## Purpose

Provide a standalone script that populates the database with example book records for development and manual testing. The script runs on demand, outside the API's normal operation.

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
