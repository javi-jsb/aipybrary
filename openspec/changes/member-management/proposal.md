## Why

`aipybrary` is evolving from a book catalog into a library with lending (see GitHub issue #21, Phase 1 of a 3-phase roadmap: `member-management` → `book-copy-management` → `lending`). Lending requires a library member to lend to, but no `Member` entity exists yet. This phase introduces it as an independent, self-contained slice so later phases (`book-copy-management` #22, `lending` #23) have a member to build on without this phase committing to any `Loan`/`BookCopy` modeling decision.

## What Changes

- Add a `Member` entity (SQLModel table) representing a library member, with API-boundary schemas `MemberCreate`, `MemberUpdate`, `MemberPublic`, and a `MemberListResponse` paginated envelope consistent with `BookListResponse`.
- Add a new vertical slice `members/` mirroring the `books/` slice: `MemberRepository` ABC (domain), `SqlModelMemberRepository` (infrastructure), `MemberService` with constructor-injected repository (application), FastAPI router.
- Expose CRUD endpoints under `/members`: `POST`, `GET` (paginated, filterable, sortable list), `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`.
- `GET /members` mirrors the **current** `/books` list-query contract: pagination (`page`/`size`), case-insensitive partial filtering by `full_name` and `email` (AND logic), and sorting (`sort_by`/`order`). This ships as a single `member-management` capability — the `books` split into `book-management` + `book-list-query` was an iterative historical accident, not a model to replicate.
- Member carries a lifecycle `status` (`active` / `suspended`). It is functionally inert in this phase but is introduced now because Phase 3 (`lending`, #23) will forbid suspended members from borrowing.
- Add a reversible Alembic migration creating the `members` table (not `SQLModel.metadata.create_all()`).
- Enforce a unique constraint on member `email`.

Out of scope: `Loan`, `BookCopy`, reservations, genre/category, author-as-entity. No changes to the `books` slice.

## Capabilities

### New Capabilities

- `member-management`: CRUD for the `Member` entity — domain model and API-boundary schemas, repository abstraction and SQL implementation, application service, HTTP endpoints (create, paginated/filterable/sortable list, get-by-id, partial update, delete), member lifecycle status, email uniqueness, and the Alembic migration for the `members` table.

### Modified Capabilities

<!-- None. This change is purely additive: a new slice and a new table. It does not alter the requirements of book-management, book-list-query, database-connectivity, database-seeding, or health-check. -->

## Impact

- **New code**: `src/app/members/` (`domain/`, `application/`, `infrastructure/`), router registration in `src/app/main.py`.
- **Database**: new `members` table via a new Alembic migration in `alembic/versions/`; reversible (downgrade drops the table).
- **API**: new `/members` endpoint family. No existing endpoints change.
- **Dependencies**: none expected — reuses existing stack (FastAPI, SQLModel, `uuid_utils`, Alembic, pytest).
- **Tests**: new test module mirroring `tests/books/`, targeting near-100% coverage.
- **Duplication**: ID/timestamp helpers, the paginated-query scaffolding, and the timestamp fields are copy-pasted verbatim from `books` (no shared module). This is a conscious trade-off; cross-slice modularization is deliberately deferred and tracked in #25 — implementers MUST NOT refactor it into shared code as part of this change.
- **Tracking**: GitHub issue #21; its own branch/PR; later archived via its own dedicated archive issue/PR per the OpenSpec workflow.
