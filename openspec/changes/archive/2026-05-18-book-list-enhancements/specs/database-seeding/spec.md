## MODIFIED Requirements

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
