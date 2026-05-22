## Context

`aipybrary` is a functionally complete library API (books, copies, members, loans) with **no authentication** — any client can read and mutate everything. The codebase uses slice-per-domain modules (`books/`, `members/`, `loans/`, `book_copies/`), each with a `domain` / `application` / `infrastructure` triad, plus a `core/` module of shared primitives (`db`, `entity`, `pagination`, `sorting`). `core/` is currently a **leaf**: slices import from it, it imports from no slice.

This is the first of two changes. `authentication` proves *who you are*; a follow-up `authorization` change enforces *what you may do*. The two are sequential and the app is not deployed, so the intermediate state (identity exists, roles not enforced) is acceptable.

## Goals / Non-Goals

**Goals:**

- A single `User` identity with credentials, covering all three actors (admin, staff, member).
- Stateless JWT authentication via the canonical FastAPI OAuth2 password flow.
- Every endpoint gated by a valid token, except `/health` and `/auth/login`.
- Lay the foundation the `authorization` change builds on: the `role` field, the `User`↔`Member` link, and a `role` claim in the token.

**Non-Goals:**

- Role/permission enforcement and ownership rules — the `authorization` change.
- Password self-management — changing a password, forced change on first login, email-based onboarding. A future `credential-lifecycle` change.
- Refresh tokens, token revocation, account self-registration.
- Staff/admin management endpoints — the `authorization` change.

## Decisions

### 1. Unified `User` table (Model A)

One `User` table holds credentials for all three roles. A `member`-role User links 1:1 to a `Member`; `staff`/`admin` Users have no `Member`.

*Rationale:* one credentials table → a single login lookup and a single, non-polymorphic `get_current_user`. `Member` keeps its meaning as the patron record, and the `loans.member_id` FK is untouched.

*Alternative rejected — two credentialed tables* (`Member` + a separate `Staff`): the token would have to encode which table the subject lives in, and `get_current_user` would be polymorphic, adding friction to every router.

### 2. `email` is a `User` attribute, not a `Member` attribute

`email` moves entirely from `Member` to `User`. `Member` loses its `email` column; a member's email is the email of its linked `User`. Validation, normalization, and the unique constraint move with it (`uq_members_email` → `uq_users_email`).

*Rationale:* staff and admin Users must have an email to log in regardless — `User` carries `email` unconditionally. Keeping a *second* `email` column on `Member` would be a duplicate that can silently drift. A single source of truth is the honest model. `MemberPublic` still exposes `email`, read through the linked `User`; `GET /members` filtering and sorting by email join to `users`.

### 3. FK direction: `Member.user_id → User.id`, `NOT NULL` + `UNIQUE`

The link is a column on `members`, not on `users`.

*Rationale:* every `Member` has exactly one account; `staff`/`admin` Users have no `Member`. The mandatory side is `Member → User`, so the FK belongs on `Member` where it can be `NOT NULL` — a member cannot exist without an account. The reverse would force a nullable column on `users`. Creation order is therefore User → Member.

### 4. `User.is_active` is distinct from `Member.status`

`is_active` gates whether an account can authenticate at all. `Member.status` (`active`/`suspended`) gates borrowing privilege. Login and `get_current_user` reject `is_active = false`; a suspended-but-active member can still log in and view their data (borrowing will be blocked by the `authorization` change).

### 5. `role` as a three-value `StrEnum`

`UserRole` is a `StrEnum` with `admin`, `staff`, `member` — consistent with the existing `MemberStatus` and `LoanStatus`. `admin` is a distinct enum value, not an `is_admin` boolean on a staff role: one field, one simple token claim, and the `authorization` change just switches on the enum.

### 6. Authentication-only scope; `role` stored but not enforced

The `role` column and the JWT `role` claim are introduced now, but no endpoint checks them — every authenticated user reaches every endpoint until the `authorization` change.

*Rationale:* conceptual purity — everything about *proving identity* lands here, everything about *permissions* lands next; each OpenSpec change stays cohesive and reviewable. Including the `role` claim now freezes the token shape so the next change does not have to reissue or migrate tokens. The usual cost of a "big first change" — migrating existing rows — is nil here: the database holds only seed data, so the dev volume is wiped and recreated.

### 7. JWT bearer, HS256, access-token only

Authentication uses `OAuth2PasswordBearer` + `OAuth2PasswordRequestForm` (FastAPI's canonical path), issuing a signed JWT carrying `sub` (user id) and `role`.

*Rationale:* HS256 (symmetric, one secret) over RS256 — a single service has no need for key-pair distribution; revisit only if the API is ever split. Access-token-only keeps this change small; refresh tokens are a self-contained later topic.

### 8. `core/security.py` is pure crypto; `get_current_user` lives in `users/`

`core/security.py` holds only pure, dependency-free primitives: `hash_password`, `verify_password`, `generate_password`, `encode_token`, `decode_token`. The `get_current_user` dependency lives in the `users/` slice.

*Rationale:* `get_current_user` must query the `UserRepository`. Placing it in `core/` would make `core/` import from a slice, inverting the established layering and breaking `core/`'s leaf property. Keeping the crypto pure in `core/` and the DB-touching dependency in `users/` preserves clean import boundaries — slices and `main.py` import the dependency from `users/`.

### 9. Central enforcement in `main.py`

The four existing routers are gated by attaching the dependency at registration: `app.include_router(router, dependencies=[Depends(get_current_user)])`. Router files are not edited. `/health` stays public; the `auth` router is registered without the gate (`/auth/login` is public, `/auth/me` injects `get_current_user` itself).

*Rationale:* a single chokepoint — impossible to forget to protect an endpoint, and a one-line diff per router. *Alternative rejected — per-router or per-endpoint dependencies:* more edits, more drift risk.

### 10. `POST /members` provisions the account; password generated and returned once

Because `Member.user_id` is required and `email` lives on `User`, a `Member` cannot be created without a `User`. `POST /members` therefore creates the `member`-role `User` and the linked `Member` in one operation. The system **generates** a random strong password (`core/security.py`), stores only its Argon2 hash, and **returns the plaintext exactly once** in the creation response for staff to relay to the member. `MemberCreate` takes `full_name`, `email`, `status?` — no password input.

*Rationale:* with email on `User`, a member without an account is a husk (no email, no login); provisioning the account *is* member creation. Generating the password (over staff typing one) keeps staff from choosing weak or patterned passwords. The known trade-off — the plaintext appears once in an HTTP response — is accepted: the genuinely clean alternatives (forced change on first login, email-based onboarding) are a state machine and an email subsystem respectively, and belong in a separate `credential-lifecycle` change. No `must_change_password` flag is added speculatively (YAGNI; unlike `role`, no imminent change consumes it).

### 11. First admin via seed; no registration endpoint

With every endpoint gated, the bootstrap account cannot come from an endpoint. `scripts/seed.py` wipes and recreates: one `admin`, sample `staff`, and members each with a linked `member`-role User. In this change the seed is the only source of `staff`/`admin` accounts; endpoint-driven staff/admin creation is the `authorization` change.

### 12. Libraries: `pyjwt` + `pwdlib[argon2]`

`pyjwt` for JWT encoding/decoding and `pwdlib` with Argon2 for password hashing — the combination the current FastAPI security tutorial recommends. `passlib` is effectively unmaintained and `python-jose` has had maintenance concerns. Random password generation uses the standard library `secrets`. All new dependencies pinned exactly in `pyproject.toml` per the project dependency policy.

### 13. Test strategy

`conftest.py` gains an authenticated-client fixture. The existing suite calls endpoints unauthenticated and would now receive `401` everywhere. Existing tests use `app.dependency_overrides[get_current_user]` to inject a canned `User` — fast, and isolates them from token mechanics. The `/auth/login` and `/auth/me` paths themselves are covered by a small set of tests that exercise the real login flow (hash verification, token issue, token decode, `is_active` rejection).

## Risks / Trade-offs

- **Weak or leaked JWT secret** → the secret is read only from the environment with no insecure production default; `.env.example` documents it and how to generate a strong value.
- **Generated password returned in the response body** → the plaintext appears once at member creation (logs, screen). Accepted deliberately; the clean alternatives are a separate `credential-lifecycle` change. Mitigated by never persisting or returning it again.
- **Stateless tokens cannot be revoked before expiry** → accepted; the access-token TTL is kept short and configurable. Revocation/refresh is a later change.
- **`role` stored but unenforced between change 1 and change 2** → a window where any authenticated user can do anything. Accepted: the changes are sequential and the app is not deployed.
- **Breaking change — all endpoints return `401` without a token** → intentional and the point of the change; there are no external consumers.
- **Every existing test must now authenticate** → one-time cost absorbed by a shared `conftest.py` fixture and the dependency-override approach.
- **HS256 shares one secret** → correct for a single-service monolith; revisit (RS256) only if the API is split into multiple services.

## Migration Plan

- One Alembic migration: `CREATE TABLE users` (with `uq_users_email`); `ALTER TABLE members` to add `user_id` (FK to `users.id`, `NOT NULL`, `UNIQUE`) and drop the `email` column and its `uq_members_email` constraint.
- Adding a `NOT NULL` column normally needs a backfill, but the agreed approach wipes the dev database volume and recreates it (`make db-down` → `make db-migrate` → `make db-seed`), so `user_id` is added `NOT NULL` directly with no backfill step.
- Downgrade reverses both: restore `members.email` (+ `uq_members_email`), drop `members.user_id`, drop `users`. `conftest.py` already runs `upgrade head` / `downgrade base` per test, so the migration is exercised by the suite.
- No production environment exists, so there is no production migration to plan.

## Open Questions

- **Access-token TTL default** — a concrete default (e.g. 30 minutes) ships in `config.py`, tunable via environment; the exact value is not load-bearing.
- **`GET /auth/me` payload** — returns the `User` only for this change. Whether it should also embed the linked `Member` summary is deferred to the `authorization` change, where "a member's own data" is defined.
