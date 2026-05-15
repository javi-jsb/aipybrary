## 1. Shared Database Infrastructure

- [x] 1.1 Add dependencies: `alembic`, `psycopg[binary]`, `uuid_utils` with exact pins to `pyproject.toml` and run `uv sync`
- [x] 1.2 Extend `Settings` in `src/app/config.py` with `POSTGRES_*` fields and `database_url` computed property
- [x] 1.3 Create `src/app/database.py` with async engine, session factory, and `get_session` FastAPI dependency
- [x] 1.4 Initialize Alembic (`alembic init -t async alembic`), configure `alembic.ini` and `env.py` to use `Settings.database_url` and `SQLModel.metadata`

## 2. Book Domain Layer

- [x] 2.1 Create `src/app/books/` package structure: `__init__.py`, `domain/`, `application/`, `infrastructure/` sub-packages with `__init__.py` files
- [x] 2.2 Create `domain/book_model.py`: `Book` (SQLModel table), `BookCreate`, `BookUpdate`, `BookPublic` schemas
- [x] 2.3 Create `domain/book_repository.py`: `BookRepository` ABC with `create`, `get_by_id`, `get_all`, `update`, `delete` abstract methods

## 3. Book Application Layer

- [x] 3.1 Create `application/book_service.py`: `BookService` with constructor-injected `BookRepository`, implementing CRUD use cases

## 4. Book Infrastructure Layer

- [x] 4.1 Create `infrastructure/sql_book_repository.py`: `SqlModelBookRepository(BookRepository)` with async SQLModel implementations
- [x] 4.2 Create `infrastructure/book_router.py`: FastAPI router with `GET /books`, `GET /books/{book_id}`, `POST /books`, `PATCH /books/{book_id}`, `DELETE /books/{book_id}`
- [x] 4.3 Register the books router in `src/app/main.py`

## 5. Database Migration

- [x] 5.1 Generate Alembic migration for the books table: `alembic revision --autogenerate -m "create books table"`
- [x] 5.2 Review and adjust the generated migration, then apply with `alembic upgrade head`

## 6. Seed Script

- [x] 6.1 Create `scripts/seed.py`: standalone async script that inserts example books, idempotent (skips if data exists)

## 7. Tests

- [x] 7.1 Add test infrastructure: async test fixtures for database session (test DB or overridden dependency)
- [x] 7.2 Tests for `BookService` (unit tests with a fake/in-memory repository)
- [x] 7.3 Tests for API endpoints (integration tests via `httpx.AsyncClient` against the FastAPI app)
