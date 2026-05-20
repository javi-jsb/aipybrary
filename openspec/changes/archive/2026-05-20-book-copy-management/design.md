## Context

aipybrary is mid-evolution from a book catalog to a lending library. Phase 1 (`member-management`) is archived; Phase 3 (`lending`) will model `Loan` against physical inventory. Phase 2 introduces `BookCopy` — the physical instance of a `Book` that a `Loan` actually references.

The roadmap originally framed each phase as one capability and *implicitly* one slice, but that conflation has been clarified during exploration. The codebase's actual organizing principle is **slice = aggregate / resource**, not slice = capability (see `book-management` and `book-list-query` co-located in `src/app/books/`). This design follows that clarified principle (recorded in the project memory `lending-domain-roadmap`).

Current state when this change starts:
- `src/app/books/` slice with `Book` CRUD + paginated list + filters/sort.
- `src/app/members/` slice with `Member` CRUD + paginated list + filters/sort.
- Pattern: domain ABC → SQLModel implementation → service → router; named unique constraints; `IntegrityError` → domain exception → HTTP 4xx in the router.
- Repetition points already accepted as deliberate, tracked by issue #25.

## Goals / Non-Goals

**Goals:**
- Introduce `BookCopy` as an independent aggregate that Phase 3 can reference by ID without coupling to `Book`'s slice.
- CRUD + paginated/filterable/sortable list under flat REST routes `/book-copies`, mirroring `/members` and `/books`.
- Enforce barcode uniqueness with a named constraint so the repository can distinguish a barcode collision from any other integrity violation (same pattern as ISBN and email).
- Enforce referential integrity: a `BookCopy` cannot exist without a `Book`, and a `Book` with copies cannot be deleted silently.
- Surface enough information at the `/books` boundary (`copies_total`) so a client can answer "how many physical instances does this title have?" in a single request, with no N+1 risk.

**Non-Goals:**
- Modelling physical condition (`damaged`, `lost`, `retired`) — out of scope this phase. If it ever becomes a requirement, it will be its own capability.
- Modelling "currently lent" on the copy — that state is derived from `Loan` (Phase 3), not stored on `BookCopy`.
- `copies_available` on `BookPublic` — deferred to Phase 3 when `Loan` exists; today it would just equal `copies_total`.
- Nested routes (`/books/{book_id}/copies`) — explicitly rejected (see Decisions).
- Acquisition tracking (`acquired_at`, supplier, cost) — not needed for the lending domain.
- Bulk operations (e.g., "create 10 copies of this book at once") — single-resource CRUD only.
- Shared primitives extraction (`_uuid7`, pagination envelope, `SortOrder`, etc.) — tracked by issue #25; this change deliberately repeats the pattern a third time rather than pulling that refactor forward.

## Decisions

### Decision: Independent slice `src/app/book_copies/`, not an extension of `books/`

`BookCopy` lives in its own slice mirroring `members/`, not nested under `books/`. Alternative considered: co-locate inside `books/` (same directory, no `relationship()`, sharing helpers).

Rationale:
- Structurally, `BookCopy` has its own model, table, repository, service, and router — i.e., the full apparatus of a slice. Co-locating only shares the directory, not the files.
- The DDD aggregate test favours separate aggregates: `DELETE Book` is `RESTRICT` (not `CASCADE`), CRUD is independent on both sides, there are no invariants that span both, and `BookCopy` is accessed by its own root route, not nested under `Book`. A `BookCopy` references a `Book` but is not *part of* `Book`'s aggregate.
- Symmetric structure (one aggregate = one slice) matches the existing pattern (`members/` = one slice, `books/` = one slice) and avoids introducing an asymmetric exception that future entities would have to justify against.
- The two main objections to a separate slice — cross-slice imports for validation, and helper duplication — are addressed below and judged acceptable.

### Decision: Cross-slice imports allowed at the **application service** layer

`BookCopyService` imports `BookRepository` (the ABC) from `src/app/books/domain/` and receives an instance via constructor injection, in order to validate that `book_id` references an existing book at creation time.

Layer-by-layer rule (recorded for future phases):

| Layer | Cross-slice import |
|---|---|
| Domain entity (e.g., `BookCopy`) | ❌ Foreign aggregates referenced by ID only (`book_id: UUID`). No imports. |
| Domain port/ABC | ❌ Don't import another slice's ABC at definition time. ✅ Other slices' services may consume your ABC. |
| Application service | ✅ Compose multiple repository ABCs to orchestrate cross-aggregate validation/invariants. This is what services are for. |
| Infrastructure | ✅ No restriction (routers share the app, repos share the DB). |

This is consistent with the project memory's rule for Phase 3 (`Loan` will reference Member/BookCopy by ID, but `LoanService` will compose multiple repos for invariant checks). The hexagonal boundary that matters — domain ↔ infrastructure — remains intact.

### Decision: No `status` field on `BookCopy` in this phase

Alternative considered: introduce `BookCopyStatus` (`available` / `damaged` / `lost` / `retired`) as a `StrEnum` with default `available`, mirroring the `MemberStatus` pattern (defined now, behavioural use in a later phase).

Rejected because:
- The use case for physical condition is not present yet. Adding a field "in case Phase 3 needs it" is speculative — Phase 3 only needs to know whether a copy is currently lent, and that comes from `Loan`, not from the copy.
- "Currently lent" is **not** a `BookCopy` status: it is derived state (mirror of the `OVERDUE` derived-state decision in the roadmap). Storing it would create a synchronisation problem that derivation avoids.
- If physical condition becomes a real requirement, it will be its own capability (additive) and won't disrupt this one.

In practice this phase: if a copy is lost or damaged, the admin deletes it. Historical loans of a deleted copy are a Phase 3 concern.

### Decision: `book_copies.book_id` FK with `ON DELETE RESTRICT`, mapped to 409 by the router

Alternatives considered: `CASCADE` (delete copies when their book is deleted), `SET NULL` (orphan copies on book deletion).

`RESTRICT` chosen:
- A library never silently destroys physical-inventory records. If a book has copies, deleting the book is an error the caller must resolve explicitly.
- `CASCADE` is dangerous: it would also wipe future `Loan` history that references those copies (Phase 3).
- `SET NULL` produces orphan copies with no semantic meaning.

Implementation: `book_copies.book_id` declared NOT NULL with a FK to `books.id ON DELETE RESTRICT`. The `SqlModelBookRepository.delete` translates the resulting `IntegrityError` into a domain exception (e.g., `BookHasCopiesError`), which the router maps to `409 Conflict`. This mirrors the existing `IntegrityError` → `DuplicateIsbnError` → 409 pattern, but checks the constraint name (FK, not a unique index) to distinguish.

### Decision: `BookPublic.copies_total` is **derived** at query time, not denormalised

Computed via a single aggregated SQL query at every read site (list and get-by-id), using a correlated subquery or a `LEFT JOIN` + `GROUP BY` — both feasible in PostgreSQL with the SQLModel async engine, no N+1.

Alternatives considered:
- Denormalised counter column on `books` updated by triggers or by the application on copy create/delete. Rejected: synchronisation risk, no real read-path performance pressure today, derived value is always correct by construction.
- `copies_available` exposed now (always equal to `copies_total` until Phase 3). Rejected: the API contract would either change semantically when Phase 3 lands (lying field) or look redundant. Adding it in Phase 3 is purely additive.

Trade-off accepted: every Book read incurs an aggregate over `book_copies`. At current scale this is negligible; if it ever shows up in profiling, a denormalised counter or a materialised view is a backward-compatible swap.

### Decision: Flat REST routes `/book-copies`, not nested under `/books`

Alternatives considered:
- Nested: `POST /books/{book_id}/copies`, `GET /books/{book_id}/copies/{copy_id}`, etc.
- Hybrid: nested for collection (`POST` / `GET` list), flat for instance (`GET /book-copies/{id}`).

Flat chosen:
- Consistent with the rest of the project (`/books`, `/members` are all flat).
- The most frequent caller in Phase 3 — `LoanService` validating a `book_copy_id` — has the copy ID and not the book ID. A nested route forces the caller to know `book_id` it doesn't need; a flat route serves the call site directly.
- `book_id` is provided in the `BookCopyCreate` body. There is no URL/body contradiction because the body is the only source.
- `BookCopyUpdate` deliberately omits `book_id` (a copy cannot be reassigned to a different book — that would be delete + create), so PATCH and DELETE only need the copy ID.

### Decision: 422 (not 404) when `book_id` does not exist on create

When `POST /book-copies` is called with a `book_id` that does not exist, the response is `422 Unprocessable Entity`, not `404`.

Rationale: `404` semantically applies to the addressed resource. The addressed resource here is the `book-copies` collection — which exists. The `book_id` value inside the body is malformed in the validation sense: it points nowhere. `422` is the right code for "your body is structurally fine but semantically rejected." This is consistent with FastAPI/Pydantic conventions for input validation failures.

The DB FK is the second line of defence: if a `book_id` slips past service-level validation (e.g., due to a race), the FK violation is also translated to `422` by the router.

### Decision: Helper duplication is acceptable for this change

`_uuid7()`, `_utcnow()`, `SortBy`/`SortOrder` enums, `ListResponse` envelope with `pages`, and the `Duplicate<X>Error` exception pattern will be duplicated a third time inside `src/app/book_copies/`. Issue #25 ("extract shared cross-slice primitives") explicitly catalogues this repetition and is tracked separately.

Rationale: introducing the abstraction now would require a third example to be confident the abstraction fits, and Phase 2 *is* that third example. Repeating once more to confirm the pattern is the lower-risk path. The duplication has zero runtime cost.

## Risks / Trade-offs

- **Slice grew the project from 2 to 3** → Increases the surface where #25 will need to be applied. Mitigation: tracked explicitly; not new debt.
- **Cross-slice service-level import sets a precedent** → Future services may abuse this for any reason, not just orchestration. Mitigation: the rule is documented in this design (layer table) and will be re-stated in the Phase 3 design when `LoanService` composes three repositories.
- **`copies_total` aggregation cost** → Every Book read does an extra COUNT against `book_copies`. Mitigation: single query (no N+1); revisit if profiling shows pressure; swap to denormalised counter or materialised view is backward-compatible.
- **`RESTRICT` on `book_id` FK may surprise clients deleting a book** → A previously-204 endpoint now returns 409 in some cases. Mitigation: documented as part of the spec delta on `book-management`; consumers should already expect 4xx on conflicting deletes in REST APIs.
- **Cascading delete is impossible by design** → Bulk teardown (e.g., wiping a book and its copies) requires multiple calls. Mitigation: not a required workflow; if needed later, a dedicated endpoint can be added.
- **No `acquired_at` means no inventory aging** → Reports like "copies acquired this quarter" are not possible. Mitigation: out of scope; can be added later additively.
- **No `status` means no soft-deletion of damaged copies** → A damaged copy must be hard-deleted, losing its UUID/barcode for audit. Mitigation: explicitly out of scope; if audit is needed later, soft-delete is an additive capability.

## Migration Plan

Single Alembic revision:

1. Create table `book_copies` with columns `id` (UUID PK), `book_id` (UUID NOT NULL, FK to `books.id` ON DELETE RESTRICT), `barcode` (varchar(100) NOT NULL), `location` (varchar(200) nullable), `notes` (TEXT nullable), `created_at` (timestamp, server default `now()`), `updated_at` (timestamp, server default `now()`).
2. Add unique constraint on `barcode` with explicit name `uq_book_copies_barcode`.
3. (Optional, for query performance) Add index on `book_id` for the FK lookup and `copies_total` aggregation. PostgreSQL creates one automatically for the FK in some configurations; an explicit index makes the intent clear.

Downgrade drops the table (the FK and unique constraint are dropped with it). No data migration needed — this is a new table.

## Open Questions

None blocking. The 404-vs-422 question was resolved in favour of 422 (see Decisions). Length cap for `location` set at 200 chars (informed guess; trivially extendable).
