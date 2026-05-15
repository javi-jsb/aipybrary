## Context

The application is a greenfield FastAPI + SQLModel REST API with a running Postgres 17 container (docker-compose.yml) but no database connectivity. The codebase has a `Settings` class (pydantic-settings), a `GET /health` endpoint, and SQLModel declared as a dependency but not imported. The `.env.example` already defines `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, and `POSTGRES_PORT`.

This change introduces the first vertical slice (books) and all the shared infrastructure it requires. It establishes the hexagonal architecture pattern that every future slice will follow.

## Goals / Non-Goals

**Goals:**
- Async PostgreSQL connectivity via SQLModel + psycopg
- Alembic migration infrastructure with the first migration (books table)
- Hexagonal vertical-slice structure with sub-packages: domain, application, infrastructure
- Full CRUD for the Book entity (list, get, create, update, delete)
- A standalone seed script for development convenience
- Tests covering all layers

**Non-Goals:**
- Pagination, filtering, or sorting on list endpoints (future enhancement)
- Authentication or authorization
- Full-text search or advanced queries
- CI/CD pipeline
- Production deployment configuration
- Relationships between entities (authors as a separate entity, etc.)

## Decisions

### 1. Hexagonal vertical-slice directory structure with sub-packages

```
src/app/
  books/
    __init__.py
    domain/
      __init__.py
      book_model.py            # Book(SQLModel, table=True), BookCreate, BookUpdate, BookPublic
      book_repository.py       # BookRepository ABC
    application/
      __init__.py
      book_service.py          # CRUD use cases
    infrastructure/
      __init__.py
      sql_book_repository.py   # SqlModelBookRepository
      book_router.py           # FastAPI endpoints
  database.py                  # Engine, async session factory, get_session
  config.py                    # Settings (existing, extended)
  main.py                      # FastAPI app (existing, extended)
```

Each vertical slice is a package (`books/`) with sub-packages for each hexagonal layer. The domain defines the entity and a repository port (ABC); the infrastructure implements the port and exposes the HTTP adapter; the application layer orchestrates domain logic through ports.

**Why sub-packages instead of flat files:** Even for a single entity, sub-packages establish the pattern that future slices inherit. When a layer grows (e.g., a second port, a query service), the files stay organized without a flat-file refactor.

**Why entity-prefixed filenames (`book_repository.py`, not `repository.py`):** When multiple slices exist and several files are open in an editor, tab labels like `repository.py` are ambiguous. `book_repository.py` is immediately identifiable without checking the path. Singular form (`book_`, not `books_`) because the file deals with the `Book` entity.

### 2. Router inside infrastructure (not separate api/ package)

The FastAPI router lives at `infrastructure/book_router.py`, alongside the repository. In hexagonal architecture, both the router (driving/inbound adapter) and the repository (driven/outbound adapter) are infrastructure — they are technical details external to the domain and application layers.

**Why not a separate `api/` package:** Keeping all adapters in `infrastructure/` follows hexagonal theory. The filenames (`book_router.py` vs `book_repository.py`) make the distinction clear. A separate `api/` package would split adapters into two locations, obscuring the architectural symmetry.

### 3. ABC for repository ports

The domain defines `BookRepository` as an `abc.ABC` — the infrastructure must explicitly inherit from it.

**Why ABC over Protocol:** ABC catches contract violations at instantiation time, without needing a type checker. If `SqlModelBookRepository` misspells or forgets a method, Python raises `TypeError` the moment you create an instance. Protocol requires mypy/pyright to catch the same error — without a type checker configured, mismatches pass silently until runtime. Since this project does not have a type checker in the pipeline yet, ABC provides a free safety net.

**Dependency direction:** The infrastructure module imports from the domain (to inherit the ABC). This is the correct direction in hexagonal architecture — infrastructure depends on domain, never the reverse.

### 4. Single SQLModel class (unified domain + persistence model)

The `Book` class in `domain/book_model.py` is both the domain entity and the database table (`SQLModel` with `table=True`). There is no separate `BookModel` in infrastructure.

**Why not two models (pure hexagonal):** The mapping layer between a domain `Book` and an infrastructure `BookModel` introduces boilerplate that scales with every field and every entity. Forgotten fields in the mapping cause silent data loss. SQLModel was designed explicitly to unify Pydantic validation and SQLAlchemy persistence in one class — fighting that design yields complexity without proportional benefit.

**What stays separate:** API schemas (`BookCreate`, `BookUpdate`, `BookPublic`) are plain Pydantic models (not `table=True`). They control what the API accepts and returns, decoupling the HTTP contract from the storage model. This is the boundary that matters most.

**Trade-off acknowledged:** The domain module imports SQLModel, coupling it to the ORM choice. In practice, changing ORM in a FastAPI+SQLModel project is not a realistic scenario, and the daily cost of mapping boilerplate outweighs the theoretical benefit.

### 5. Shared database module at `src/app/database.py`

Engine creation, async session factory, and the `get_session` FastAPI dependency live in a single shared module.

**Why shared:** The engine and session factory are cross-cutting infrastructure. Every slice needs a session, and there must be exactly one engine per process. Placing it inside `books/` would force future slices to import from an unrelated slice.

### 6. Async engine and sessions

SQLModel's `create_async_engine` with `psycopg` as the async driver. Sessions are `AsyncSession` from `sqlalchemy.ext.asyncio`, exposed as a FastAPI dependency via `async def get_session()`.

**Why async:** FastAPI is async-native. Sync database calls in async endpoints block the event loop. Since this is also a learning project, using async from the start teaches the correct pattern.

**Why psycopg (v3) over asyncpg:** psycopg v3 is the modern successor to psycopg2, supports async natively, and is the recommended driver for SQLAlchemy/SQLModel async. It uses the `postgresql+psycopg://` dialect string.

### 7. DATABASE_URL composed in Settings

The `Settings` class gains a `database_url` computed property that assembles the URL from the individual `POSTGRES_*` environment variables already in `.env.example`. The async variant uses the `postgresql+psycopg://` scheme.

**Why compose instead of a single `DATABASE_URL` env var:** The individual variables are already defined for Docker Compose. Composing the URL avoids duplication and keeps a single source of truth.

### 8. Alembic with async support and autogenerate

Alembic initialized at the project root (`alembic/` directory, `alembic.ini`). The `env.py` is configured for async operation. Migrations target `SQLModel.metadata`.

Autogenerate compares the current SQLModel models against the actual database state and produces a migration script with the diff. The developer must always review the generated migration before applying it — autogenerate is a starting point, not a final product.

**Migration workflow:**
1. Modify the SQLModel model in code
2. `alembic revision --autogenerate -m "description"` — generates a migration file
3. Review the generated file (autogenerate can misinterpret renames as drop+create)
4. `alembic upgrade head` — applies the migration

**Why project root for `alembic/`:** Convention. Alembic expects `alembic.ini` at the working directory.

### 9. UUIDv7 primary keys via `uuid_utils`

Book IDs use UUIDv7, generated in Python via the `uuid_utils` library.

**Why UUIDv7 over v4:** UUIDv7 embeds a millisecond timestamp, making IDs time-ordered. This means sequential B-tree inserts (no index fragmentation), natural sort-by-creation, and the ability to extract creation time from the ID itself. UUIDv4 is random, causing scattered index writes.

**Why generated in Python, not Postgres:** PostgreSQL 17 has no native UUIDv7 function. PostgreSQL 18 adds `uuidv7()` but is still in beta (stable expected late 2025). Generating in Python with `uuid_utils` (a fast Rust-backed library) works on any Postgres version and keeps the logic in the application.

### 10. Book model fields

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | PK, default `uuid_utils.uuid7()` |
| `title` | `str` | Required, max 500 chars |
| `author` | `str` | Required, max 300 chars |
| `isbn` | `str \| None` | Optional, max 13 chars, unique when present |
| `publication_year` | `int \| None` | Optional |
| `created_at` | `datetime` | Server-default `now()`, not updatable |
| `updated_at` | `datetime` | Server-default `now()`, auto-updated |

**Why `isbn` optional:** Not all books have ISBNs (pre-1970, self-published, etc.). Unique constraint when present prevents duplicates. Postgres handles `UNIQUE` on nullable columns correctly (multiple NULLs allowed).

### 11. API endpoints and schemas

| Method | Path | Status | Response |
|---|---|---|---|
| `GET` | `/books` | `200` | `list[BookPublic]` |
| `GET` | `/books/{book_id}` | `200` / `404` | `BookPublic` |
| `POST` | `/books` | `201` | `BookPublic` |
| `PATCH` | `/books/{book_id}` | `200` / `404` | `BookPublic` |
| `DELETE` | `/books/{book_id}` | `204` / `404` | _(no content)_ |

**Why PATCH over PUT:** PATCH allows partial updates (send only changed fields). SQLModel's `model.sqlmodel_update()` supports this natively.

**Schemas:**
- `BookCreate`: fields the client sends to create (title, author, isbn, publication_year)
- `BookUpdate`: all fields optional (partial update)
- `BookPublic`: what the API returns (all fields including id, created_at, updated_at)

### 12. Standalone seed script

`scripts/seed.py` — a plain Python script that imports the app's database module and Book model, creates an async session, and inserts a predefined list of example books. Idempotent: checks if data already exists before inserting.

**Run:** `uv run python scripts/seed.py`

**Why standalone over a CLI framework:** Simplicity — the seed is the only script needed now. If `scripts/` grows beyond ~5 scripts, migrating to Typer is a trivial refactor because the logic lives in the app, not in the script.

## Risks / Trade-offs

- **Async adds complexity for a learning project** → Accepted: learning async is part of the educational goal, and the patterns are well-documented in the FastAPI and SQLAlchemy ecosystem.
- **UUIDv7 adds a dependency (`uuid_utils`)** → Small, Rust-backed library with no transitive dependencies. When PG18 is stable and adopted, generation could move to the database.
- **Alembic autogenerate may produce imperfect migrations** → Mitigated: every generated migration must be reviewed before committing. This is itself a learning opportunity.
- **No pagination on list endpoint** → Acceptable for the first version. A natural follow-up change when book count grows.
- **Single model couples domain to SQLModel** → Accepted: the mapping boilerplate of a dual-model approach costs more than the theoretical purity. API schemas remain separate, protecting the HTTP boundary.
- **Sub-package structure is deep for one entity** → Accepted: establishes the pattern from day one. Future slices copy the structure without restructuring.

## Open Questions

_(none — all decisions resolved during explore session)_
