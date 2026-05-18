## Context

The current `GET /books` endpoint fetches the entire `books` table and returns it as a flat JSON array. The `Book` model has no synopsis field and no validation beyond max-length on ISBN. The seed script has 5 books, all Hispanic literature, insufficient for testing filters and sorting meaningfully.

This change touches the domain model (new field, new validator), the repository contract (new query method), the application service, the HTTP router, a database migration, and the seed script.

## Goals / Non-Goals

**Goals:**
- Paginated, filterable, sortable `GET /books` with an envelope response
- ISBN-10 and ISBN-13 checksum validation at the Pydantic layer
- `synopsis` field on the Book model with Alembic migration
- Expanded seed dataset useful for manual exploration

**Non-Goals:**
- Full-text search (ILIKE partial match is sufficient)
- Cursor-based pagination
- Filtering or sorting on `synopsis`
- Authentication or per-user visibility

## Decisions

### Pagination style: offset (page/size) over cursor

Cursor pagination is more scalable but adds significant complexity (encoding, stable sort requirement). For a learning project with small datasets, offset pagination is simpler and teaches the core concepts. `page` starts at 1; `size` is capped at 100 to avoid accidental full-table fetches.

### Response envelope as a typed Pydantic model

The envelope is defined as `BookListResponse(items, total, page, size, pages)` — a proper Pydantic model, not a raw dict. This keeps FastAPI's response schema generation working and makes the shape explicit.

### Filtering: ILIKE via SQLAlchemy, not Python-side

Filtering happens in the database query (SQLAlchemy `ilike`), not by fetching all rows and filtering in Python. This keeps the `total` count correct and avoids loading unnecessary data.

### ISBN validation: pure Python, no new dependency

ISBN-10 and ISBN-13 checksums are simple arithmetic. Implementing them as a `@field_validator` in the Pydantic model keeps the dependency count zero and the logic in the domain layer where it belongs. Hyphens are stripped before validation and storage.

### `get_all` replaced by `get_filtered`

The repository ABC gains a single `get_filtered(filters, sort, page, size) -> (list[Book], int)` method that returns both the page of results and the total count in one call (two SQL queries: one with `COUNT(*)`, one with `LIMIT/OFFSET`). `get_all` is removed — nothing outside tests used it directly.

### synopsis: nullable text, no length cap

`synopsis` is an optional free-text field. Capping its length would be arbitrary for a library project; the database column is `TEXT` (unbounded). Pydantic accepts `str | None`.

## Risks / Trade-offs

- **BREAKING response shape** → Any existing client of `GET /books` breaks. Acceptable: this is a development-stage project with no external consumers.
- **Two queries per list call** (COUNT + SELECT) → Minor overhead at this scale; avoids the complexity of window functions.
- **ILIKE on unindexed columns** → Slow on large datasets. Acceptable now; a future change can add indexes if needed.

## Migration Plan

1. Generate Alembic migration: `alembic revision --autogenerate -m "add synopsis to books"`
2. Review generated migration for correctness
3. Apply: `alembic upgrade head`
4. Rollback: `alembic downgrade -1` drops the column

No data migration needed — `synopsis` is nullable with no default required.
