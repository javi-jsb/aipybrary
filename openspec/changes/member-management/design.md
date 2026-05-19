## Context

`aipybrary` currently has a single domain slice, `books/`, built with a vertical-slice + hexagonal layout (`domain` / `application` / `infrastructure`) and Alembic-managed schema. This change adds the first slice of the catalog→library evolution: `Member` (GitHub issue #21, Phase 1 of `member-management` → `book-copy-management` #22 → `lending` #23).

The dominant constraint is **consistency**: the `books` slice already encodes the project's conventions (UUIDv7 PK via `uuid_utils`, server-default timestamps with `onupdate`, separate `*Create`/`*Update`/`*Public` schemas, paginated envelope, repository ABC + SQLModel implementation, service with constructor-injected repo, Alembic migration). Phase 1 should follow that template rather than invent anything.

## Goals / Non-Goals

**Goals:**

- A `members/` slice structurally identical to `books/` so the pattern is reinforced, not forked.
- A `Member` with a lifecycle `status` (`active`/`suspended`) wired in now so Phase 3 needs no member migration.
- Reversible Alembic migration with a unique constraint on `email`.
- Near-100% test coverage mirroring `tests/books/`.

**Non-Goals:**

- No `Loan`, `BookCopy`, reservations, genre/category, or author-as-entity.
- No shared/refactored cross-slice code (ID/timestamp helpers, generic pagination, base model): `members` duplicates `books` verbatim; modularization is deliberately deferred and tracked in #25.
- No behavioural effect of `status` yet — it is inert until `lending` (#23).
- No changes to the `books` slice (any backport of patterns introduced here is a separate tracked follow-up, per the #24 precedent).

## Decisions

**Mirror the `books` slice verbatim.** Same file layout (`domain/member_model.py`, `domain/member_repository.py`, `application/member_service.py`, `infrastructure/sql_member_repository.py`, `infrastructure/member_router.py`), same UUIDv7/timestamp helpers, same schema split. Alternative considered: a shared generic base/CRUD abstraction across slices — rejected for Phase 1 as premature; only two slices exist and an abstraction now would be speculative. Revisit if a third slice repeats the same boilerplate.

**Introduce `status` now, inert.** A `MemberStatus` `StrEnum` (`active`/`suspended`), default `active`. Alternative: add it in Phase 3 when first needed — rejected because that forces a second migration on an entity whose shape we already know; the cost of carrying an inert column now is near zero.

**Map duplicate `email` to HTTP 409 via a domain exception.** The unique constraint is enforced at the DB layer. The SQL repository (infrastructure) catches SQLAlchemy's `IntegrityError` and re-raises a domain-level `DuplicateEmailError`; the router maps that to a `409 Conflict` for `POST` and `PATCH`. The service stays untouched — catching `IntegrityError` in the service would couple the application layer to SQLAlchemy, violating the "service depends only on the domain ABC" requirement. Alternative: pre-check with a `SELECT` before insert — rejected (race condition; the DB constraint is the source of truth). Note: `book-management` currently does not define an explicit 409 for duplicate ISBN. We deliberately choose the explicit-409 behaviour for members; backporting it to books is out of scope here (tracked in #24).

**Reuse the `BookListResponse` envelope shape.** `MemberListResponse` has the same `items`/`total`/`page`/`size` + computed `pages` structure for API consistency. Alternative: a shared generic `Page[T]` model — deferred along with the broader "shared CRUD" question above.

**Ship the full list-query contract as one capability.** `GET /members` mirrors the *current* `/books` behaviour: pagination + case-insensitive partial filtering (`full_name`, `email`, independent and AND-combined) + sorting (`sort_by` ∈ `full_name`/`email`/`created_at`, `order` ∈ `asc`/`desc`, default `created_at`/`desc`). All of it lives in the single `member-management` capability. Alternative considered: replicate the `books` split into a separate `member-list-query` capability — rejected, because that split in `books` was an iterative accident (pagination/filter/sort were added later in a second change, #18), not a deliberate boundary. Copying an accident is not consistency.

**Accept verbatim duplication; defer modularization (tracked #25).** The `_uuid7()`/`_utcnow()` helpers, the `get_filtered` count+slice+order scaffolding, and the `created_at`/`updated_at` field definitions are copy-pasted from `books`. This *refines* the earlier "shared base = premature" stance: still deferred, but now explicitly tracked in #25 (with the three repetition points and their option sets) rather than left to a vague "revisit later". Rationale: keep #21 focused; avoid abstracting from a biased 2-slice sample (`books`/`members` are deliberately near-identical — `loans` will be a better stress test); follow the established #24 "improve-then-backport-separately" precedent.

## Risks / Trade-offs

- **Boilerplate duplication between `books` and `members`** → Accepted; no longer a vague "future trigger" but a concretely tracked item (#25) capturing the three repetition points, their option sets, and the consistency tension. Re-evaluate when `book-copy-management` (#22) lands.
- **409 behaviour diverges from `books`** → Documented as an intentional, isolated improvement; tracked as an open question rather than silently inconsistent.
- **Migration ordering** → The new migration must depend on the current Alembic head; `alembic upgrade head` then `downgrade -1` is verified in tests/locally before merge (reversibility is a spec scenario).

## Migration Plan

1. Create the `members/` slice and `Member` model.
2. Generate/author the Alembic migration against the current head; verify `upgrade head` then `downgrade -1` round-trips cleanly.
3. Register the router in `src/app/main.py`.
4. Ship behind its own branch/PR referencing `Closes #21`; archive the change later via its own dedicated archive issue/PR.

Rollback: `alembic downgrade -1` drops the `members` table; the slice code is removed with the PR revert. No data migration (new table, no dependents in Phase 1).

## Open Questions

- Aligning `book-management` to also return `409` on duplicate ISBN is **tracked in #24** (a separate `fix:` change — books likely returns an unhandled 500 today). Out of scope here and non-blocking; the divergence is not live until this change ships.
- ~~Default/max `size` for the members list endpoint~~ **Resolved**: confirmed against `src/app/books/infrastructure/book_router.py:32-37` — `page` default `1` (`>= 1`), `size` default `20` (`>= 1`, `<= 100`), `sort_by` default `created_at`, `order` default `desc`. `members` adopts these identically.
