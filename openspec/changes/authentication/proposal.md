## Why

`aipybrary` is functionally complete as a library domain — books, copies, members, loans — but completely open: any unauthenticated client can read and mutate everything, including creating loans on behalf of arbitrary members. This change introduces **authentication**: a `User` identity with credentials, JWT-based login, and a requirement that every endpoint present a valid token.

It is the **first of two changes**. This one proves *who you are*; a follow-up `authorization` change enforces *what you may do* (roles and ownership). The `role` field is introduced here but intentionally **not enforced** — every authenticated user can still reach every endpoint until the next change.

## What Changes

- **New slice `users/`** with the `User` entity, `UserRepository`, an authentication service, the auth router, and the `get_current_user` dependency.
- **New `core/security.py`** — pure, dependency-free primitives: password hashing and verification (`pwdlib` with Argon2), random password generation, and JWT encode/decode (HS256). A leaf module; `get_current_user` lives in `users/` instead, since it needs the repository.
- **`POST /auth/login`** — OAuth2 password flow (`OAuth2PasswordRequestForm`); verifies credentials and returns a JWT access token. Public.
- **`GET /auth/me`** — returns the authenticated user.
- **Email moves from `Member` to `User`.** `User` owns `email` as the login identity, with validation, normalization, and a unique constraint (`uq_users_email`). `Member` no longer stores `email`; a member's email is the email of its linked `User`. Staff and admin need an email to log in regardless, so a single email column on `User` removes the duplication rather than keeping a second copy that can drift.
- **`Member` gains `user_id`** — `NOT NULL`, `UNIQUE` FK to `User` — and loses its `email` column. Every member is linked 1:1 to a `member`-role User; staff/admin Users have no `Member`.
- **`POST /members` provisions the account.** Because `user_id` is required, creating a member now also creates its `member`-role `User`: the system **generates a random initial password**, stores only its hash, and **returns the plaintext once** in the creation response so staff can relay it to the member. `MemberCreate` takes `full_name`, `email`, and an optional `status` — no password input.
- **Every existing endpoint requires a valid bearer token** — `books`, `book_copies`, `members`, `loans`. Enforced centrally in `main.py` via `include_router(..., dependencies=[...])`; the router files themselves are untouched. `/health` and `/auth/login` stay public.
- **`User.role`** — `StrEnum` `{admin, staff, member}`, stored but not enforced this change. The JWT carries `sub` (user id) and a `role` claim now, so the token shape does not change in the authorization change.
- **`User.is_active`** gates whether an account can authenticate at all — distinct from `Member.status`, which gates borrowing privileges.
- **Three new settings** in `config.py` (JWT secret, algorithm, access-token expiry), sourced from the environment; `.env` / `.env.example` updated.
- **Delta to `database-seeding`**: the seed wipes and recreates from scratch — the first `admin`, sample `staff`, and every seeded member linked to its own `member`-role User. Seeding order becomes users → books → members → book copies → loans.
- **Alembic migration**: reversible — `CREATE TABLE users`; `ALTER TABLE members` to add `user_id` (FK, `NOT NULL`, `UNIQUE`) and drop `email` and its `uq_members_email` constraint.
- **Test fixture**: an authenticated test client / `get_current_user` override, so the existing suite keeps passing under the new auth gate.
- **New dependencies** (`pyjwt`, `pwdlib[argon2]`) added to `pyproject.toml` with exact pins; `uv.lock` updated. Dependency diff to be reviewed before merge.

## Out of Scope

Deferred to the follow-up `authorization` change or a later `credential-lifecycle` change:

- Role enforcement — staff/admin/member permission rules and ownership checks ("a member sees only their own data") — the `authorization` change.
- Admin-driven staff management endpoints — the `authorization` change.
- Password self-management — changing a password, forced change on first login, email-based account onboarding. In this change the initial password is system-generated and surfaced once at creation; member-owned passwords are a future `credential-lifecycle` change.
- Refresh tokens, token revocation, and account self-registration.

## Capabilities

### New Capabilities

- `authentication`: The `User` identity (`email`, `password_hash`, `role`, `is_active`), email validation/normalization/uniqueness, password hashing and random generation, JWT issuance and verification, the `POST /auth/login` and `GET /auth/me` endpoints, and the system-wide rule that all endpoints except `/health` and `/auth/login` reject requests without a valid token.

### Modified Capabilities

- `member-management`: `Member` loses its `email` column (email is now a `User` attribute) and gains a required, unique `user_id`. `POST /members` provisions the linked `member`-role account and returns a one-time generated password. A member can no longer exist without a backing account.
- `database-seeding`: `seed.py` gains a `SAMPLE_USERS` block (first admin, sample staff) and links every seeded member to its own `member`-role User. Seeding order updated to create users first.

## Impact

- **New code**: `src/app/users/` (domain, application, infrastructure layers); `src/app/core/security.py`; one Alembic migration.
- **Modified code**: `src/app/members/` (domain model loses `email`, gains `user_id`; service and SQL repository provision and join the `User`); `src/app/config.py` (three settings); `scripts/seed.py` (users block + linking); `src/app/main.py` (auth router registration + central auth dependency on the other four routers).
- **API surface**: two new endpoints under `/auth`; `POST /members` request body drops to `full_name`/`email`/`status` and its response gains a one-time `initial_password`; all existing endpoints now require `Authorization: Bearer <token>`.
- **Breaking change**: every existing endpoint returns `401 Unauthorized` without a token. This is intentional and the point of the change.
- **Dependencies**: `pyproject.toml` and `uv.lock` change — `pyjwt`, `pwdlib[argon2]` added with exact pins.
