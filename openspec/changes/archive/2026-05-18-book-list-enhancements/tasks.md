## 1. Domain model

- [x] 1.1 Add `synopsis: str | None` field to `Book`, `BookCreate`, `BookUpdate`, `BookPublic`
- [x] 1.2 Implement ISBN checksum validator (`@field_validator`) in `BookCreate` and `BookUpdate`: strip hyphens, validate length (10 or 13), validate ISBN-10 (mod 11) and ISBN-13 (mod 10) checksums
- [x] 1.3 Add `BookListResponse` Pydantic model: `items`, `total`, `page`, `size`, `pages`

## 2. Repository contract

- [x] 2.1 Remove `get_all` abstract method from `BookRepository` ABC
- [x] 2.2 Add `get_filtered(title, author, sort_by, order, page, size) -> tuple[list[Book], int]` abstract method to `BookRepository` ABC

## 3. Infrastructure — SQL repository

- [x] 3.1 Implement `get_filtered` in `SqlModelBookRepository`: build WHERE clause with ILIKE for title/author, apply ORDER BY, execute COUNT query for total, execute paginated SELECT

## 4. Application service

- [x] 4.1 Remove `get_all` method from `BookService`
- [x] 4.2 Add `get_filtered(...)` method to `BookService` that delegates to the repository and computes `pages = ceil(total / size)`

## 5. HTTP router

- [x] 5.1 Update `GET /books` endpoint: add `page`, `size`, `title`, `author`, `sort_by`, `order` query parameters with validation (page ≥ 1, 1 ≤ size ≤ 100, sort_by enum, order enum)
- [x] 5.2 Change response model from `list[BookPublic]` to `BookListResponse`

## 6. Database migration

- [x] 6.1 Generate Alembic migration: `alembic revision --autogenerate -m "add synopsis to books"`
- [x] 6.2 Review generated migration file for correctness (nullable column, no default)

## 7. Seed script

- [x] 7.1 Replace the 5-book dataset with 20 books: diverse genres and cultures, ≥3 without isbn, ≥3 without publication_year, ≥6 without synopsis, years spanning ≥5 decades

## 8. Tests

- [x] 8.1 Unit tests for ISBN validator: valid ISBN-13 (with hyphens), valid ISBN-10, invalid checksum, wrong length, null bypass
- [x] 8.2 Integration tests for `GET /books` pagination: default params, second page, empty db, page=0 → 422, size=101 → 422
- [x] 8.3 Integration tests for `GET /books` filtering: by author, by title, combined, no matches
- [x] 8.4 Integration tests for `GET /books` sorting: sort by title asc, default sort (created_at desc), invalid sort_by → 422
- [x] 8.5 Integration test: `POST /books` with synopsis, `POST /books` without synopsis
- [x] 8.6 Update any existing tests that called `get_all` or expected `list[BookPublic]` from `GET /books`
