> **Duplication guardrail (#25):** copy the `_uuid7()`/`_utcnow()` helpers, the `get_filtered` count+slice+sort scaffolding, and the `created_at`/`updated_at` field definitions **verbatim** from `books`. Do NOT extract them into a shared module — cross-slice modularization is deliberately deferred and tracked in #25.

## 1. Domain layer

- [x] 1.1 Create `src/app/members/` package with `domain/`, `application/`, `infrastructure/` subpackages mirroring `src/app/books/`
- [x] 1.2 Add `MemberStatus` `StrEnum` (`active`, `suspended`), plus `SortBy` (`full_name`, `email`, `created_at`) and `SortOrder` (`asc`, `desc`) `StrEnum`s in `domain/member_model.py`, mirroring the `books` enums
- [x] 1.3 Define `Member` SQLModel table: UUIDv7 `id` (copy the `_uuid7` helper from books verbatim), `full_name` (≤300), `email` (≤320, unique), `status` (default `active`), `created_at`/`updated_at` with server-default `now()` and `onupdate`
- [x] 1.4 Define `MemberCreate`, `MemberUpdate`, `MemberPublic` schemas and `MemberListResponse` envelope (`items`/`total`/`page`/`size` + computed `pages`), consistent with the book schemas
- [x] 1.5 Define `MemberRepository` ABC in `domain/member_repository.py` with `create`, `get_by_id`, `get_filtered` (filter by `full_name`/`email`, sort, paginate — same signature shape as `BookRepository.get_filtered`), `update`, `delete`

## 2. Application layer

- [x] 2.1 Implement `MemberService` in `application/member_service.py` with constructor-injected `MemberRepository`, exposing create / get_by_id / `get_filtered` (full_name, email, sort_by, order, page, size → `MemberListResponse`) / update / delete; no SQLModel/FastAPI imports

## 3. Infrastructure layer

- [x] 3.1 Implement `SqlModelMemberRepository` in `infrastructure/sql_member_repository.py` using async SQLModel sessions, mirroring `SqlModelBookRepository.get_filtered` verbatim: build `conditions` from `full_name`/`email` `ILIKE`, dynamic `order_by` via `getattr`, count stmt + offset/limit page slice
- [x] 3.2 Implement the FastAPI router in `infrastructure/member_router.py`: `POST /members` (201), `GET /members` with query params `page` (`ge=1`, default 1), `size` (`ge=1`, `le=100`, default 20), `full_name`, `email`, `sort_by` (default `created_at`), `order` (default `desc`) — matching `book_router.py` defaults; `GET /members/{id}` (200/404), `PATCH /members/{id}` (200/404), `DELETE /members/{id}` (204/404)
- [x] 3.3 Map duplicate-`email` `IntegrityError` to HTTP `409` for `POST` and `PATCH` (via a domain `DuplicateEmailError` raised by the repo, mapped in the router — keeps the service infra-free)
- [x] 3.4 Register the members router in `src/app/main.py`

## 4. Database migration

- [x] 4.1 Author an Alembic migration creating the `members` table with all columns and a unique constraint on `email`, depending on the current Alembic head
- [x] 4.2 Verify reversibility: `alembic upgrade head` then `alembic downgrade -1` drops the `members` table cleanly

## 5. Tests

- [x] 5.1 Create `tests/members/` mirroring `tests/books/`
- [x] 5.2 Domain/model tests: UUIDv7 id, timestamps set, `status` defaults to `active`, invalid status rejected
- [x] 5.3 Repository contract test: subclass missing methods raises `TypeError`
- [x] 5.4 Service tests: create delegates to repo; `get_by_id` returns `None` for missing
- [x] 5.5 API tests for every spec scenario: create (201 / 422 missing fields / 409 duplicate email), list — pagination (empty, default page, second page, `page=0` → 422, `size=101` → 422), filtering (`full_name`, `email`, combined AND, no matches), sorting (`full_name asc`, default `created_at desc`, invalid `sort_by` → 422); get (200/404), patch (partial update / 404 / 409 duplicate email / suspend), delete (204/404)
- [x] 5.6 Migration test: table created with `email` unique constraint; downgrade drops it

## 7. Seeding (database-seeding delta)

- [x] 7.1 Add a `SAMPLE_MEMBERS` list to `scripts/seed.py` (12 members: 9 `active` + 3 `suspended`, unique emails), reusing `app.members.domain.member_model` and the app database module
- [x] 7.2 Refactor `seed()` to per-entity idempotency: seed books iff no books exist, seed members iff no members exist (independent checks; preserves the existing book-seeding behaviour) — verified live: members seeded with books already present; second run idempotent
- [x] 7.3 Add the `database-seeding` delta spec under `specs/database-seeding/spec.md` (ADDED requirements only) and reflect it in `proposal.md` (Modified Capabilities) and `design.md`

## 6. Verification & docs

- [x] 6.1 `make check` passes (lint + format) and `make coverage` is at/near 100% for the new slice
- [x] 6.2 Update `CLAUDE.md` if any new convention/decision emerged during implementation — reviewed: no project-wide convention emerged. The 409-via-`DuplicateEmailError` placement and the deferred-modularization decision are change-scoped and captured in `design.md` + issue #25; nothing to add to `CLAUDE.md`.
- [x] 6.3 Open the PR with `Closes #21` in the body (not in commits), Conventional Commits title, commits grouped by the sections above — PR #26

## 8. PR #26 review follow-ups

- [x] 8.1 Email validation/normalization on `MemberCreate`/`MemberUpdate` (trim + lowercase + `local@domain.tld` shape), mirroring the `books` `isbn` validator; dedicated `tests/members/test_email_validator.py`
- [x] 8.2 `status` query param added to `GET /members` filter (exact match) and `sort_by` (`SortBy.status`), threaded through repo ABC / SQL repo / service / router; API + service tests
- [x] 8.3 Name the email unique constraint `uq_members_email`; SQL repo only raises `DuplicateEmailError` for that constraint and re-raises any other `IntegrityError`; white-box `tests/members/test_member_repository.py`
- [x] 8.4 Pin `test_members_migration_is_reversible` to the explicit members revision/down_revision instead of relative `-1`/`head`
