# Database Connectivity

## Purpose

Provide async PostgreSQL connectivity for the application, including engine management, session lifecycle, schema migrations via Alembic, and database configuration through environment variables.

## Requirements

### Requirement: Async database engine

The application SHALL create a single async SQLModel engine per process using the `postgresql+psycopg://` dialect, configured from environment variables.

The engine MUST be created lazily (not at import time) and MUST be reusable across all vertical slices.

#### Scenario: Engine connects to PostgreSQL

- **WHEN** the application starts and a database-dependent request arrives
- **THEN** the engine establishes a connection to the PostgreSQL instance defined by the `POSTGRES_*` environment variables

#### Scenario: Engine uses async driver

- **WHEN** the engine is created
- **THEN** it uses the `postgresql+psycopg://` async dialect (psycopg v3)

### Requirement: Async session dependency

The application SHALL expose an async session factory as a FastAPI dependency (`get_session`) that provides an `AsyncSession` per request.

The session MUST be scoped to the request lifecycle: opened before the endpoint handler runs and closed (with commit or rollback) after it completes.

#### Scenario: Session is provided to endpoint

- **WHEN** an endpoint declares a dependency on `get_session`
- **THEN** it receives an `AsyncSession` bound to the current request

#### Scenario: Session commits on success

- **WHEN** the endpoint handler completes without raising an exception
- **THEN** the session is committed and closed

#### Scenario: Session rolls back on failure

- **WHEN** the endpoint handler raises an exception
- **THEN** the session is rolled back and closed

### Requirement: Database configuration via environment variables

The `Settings` class SHALL expose a `database_url` property that composes the async connection URL from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, and `POSTGRES_DB`.

These variables MUST already exist in `.env.example`. No new environment variables SHALL be introduced.

#### Scenario: URL is composed from individual variables

- **WHEN** the application reads settings
- **THEN** `database_url` returns `postgresql+psycopg://USER:PASS@HOST:PORT/DB` using the configured values

### Requirement: Alembic migration infrastructure

The project SHALL include Alembic configured for async migrations, with `alembic.ini` and `alembic/` directory at the project root.

Alembic MUST target `SQLModel.metadata` so that autogenerate can detect model changes.

The `env.py` MUST use the application's `Settings` to obtain the database URL (single source of truth).

#### Scenario: Generate a migration from model changes

- **WHEN** a developer runs `alembic revision --autogenerate -m "description"`
- **THEN** Alembic compares the current models against the database state and generates a migration script

#### Scenario: Apply pending migrations

- **WHEN** a developer runs `alembic upgrade head`
- **THEN** all pending migrations are applied to the database in order

#### Scenario: Rollback a migration

- **WHEN** a developer runs `alembic downgrade -1`
- **THEN** the most recent migration is reverted
