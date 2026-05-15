## Why

The application has a running FastAPI skeleton and a Postgres container but no domain entities, no database connectivity, and no way to manage data. Until the first vertical slice is in place, there is nothing to build on. Books are the core entity of a library API — implementing full CRUD for them forces every architectural layer (domain, application, infrastructure, API) to exist and proves the hexagonal architecture works end-to-end. This change also introduces Alembic for schema migrations as a learning goal.

## What Changes

- Wire the application to PostgreSQL via SQLModel async sessions and the existing Docker Compose Postgres service
- Configure Alembic for schema migrations (replaces any future `create_all` approach)
- Establish the hexagonal + vertical-slice directory structure under `src/app/books/`
- Add a `Book` domain entity with fields: id, title, author, isbn, publication_year, created_at, updated_at
- Expose five REST endpoints: list, get by id, create, update, delete
- Add a standalone `scripts/seed.py` to populate the database with example books on demand
- Add new dependencies: `alembic`, `psycopg[binary]` (async Postgres driver)

## Capabilities

### New Capabilities

- `database-connectivity`: Async SQLModel engine, session factory, Alembic migration infrastructure, and database settings wired into the existing `Settings` class
- `book-management`: CRUD operations for the Book entity — domain model, repository port/adapter, application use cases, and FastAPI router
- `database-seeding`: Standalone script to create example book records for development and testing

### Modified Capabilities

_(none — no existing spec requirements change)_

## Impact

- **Code**: New package `src/app/books/` with domain, application, infrastructure, and api sub-modules. New shared database module (engine, session). Alembic directory at project root. New `scripts/` directory.
- **Configuration**: `Settings` class gains `POSTGRES_*` / `DATABASE_URL` fields. `.env.example` already has the variables; no new env vars needed beyond what exists.
- **Dependencies**: `alembic` and `psycopg[binary]` added to `pyproject.toml` with exact pins. `uv.lock` updated.
- **Database**: New `books` table managed by Alembic migration.
- **API**: New routes under `/books` (5 endpoints). Existing `GET /health` unchanged.
