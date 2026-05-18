## Why

The books list endpoint returns all records with no pagination, filtering, or ordering — not useful for manual exploration and unrealistic as a learning target. The book model is also thin (no synopsis) and ISBN is stored without any format or checksum validation, making it easy to persist invalid data.

## What Changes

- **BREAKING** `GET /books` response changes from `list[BookPublic]` to a paginated envelope `{ items, total, page, size, pages }`
- `GET /books` gains query parameters: `page`, `size`, `author` (partial, case-insensitive), `title` (partial, case-insensitive), `sort_by` (`title` | `author` | `publication_year` | `created_at`), `order` (`asc` | `desc`)
- `Book`, `BookCreate`, `BookUpdate`, `BookPublic` gain an optional `synopsis: str | None` field
- ISBN fields in `BookCreate` and `BookUpdate` are validated with full checksum logic: ISBN-10 (mod 11) and ISBN-13 (mod 10, alternating weights 1/3); hyphens are accepted and stripped before storage
- New Alembic migration adds the `synopsis` column to the `books` table
- Seed script expanded to 20 books: diverse genres and cultures, ~30% without ISBN, ~20% without publication year, ~40% without synopsis

## Capabilities

### New Capabilities

- `book-list-query`: Pagination, filtering, and sorting on `GET /books`, plus the paginated response envelope schema

### Modified Capabilities

- `book-management`: New `synopsis` field on all Book schemas; ISBN checksum validation on create/update inputs; `GET /books` response shape changes (envelope)
- `database-seeding`: Seed dataset expanded to 20 books covering the new synopsis field and edge-case coverage for filters and sort

## Impact

- `src/app/books/domain/book_model.py` — synopsis field, ISBN validator
- `src/app/books/application/book_service.py` — new `get_filtered` method replacing `get_all`
- `src/app/books/domain/book_repository.py` — new abstract method for filtered list
- `src/app/books/infrastructure/sql_book_repository.py` — filtered/sorted/paginated query
- `src/app/books/infrastructure/book_router.py` — updated `GET /books` endpoint signature and response model
- `alembic/versions/` — new migration for `synopsis` column
- `scripts/seed.py` — expanded dataset
- Tests for all new/modified behaviour
