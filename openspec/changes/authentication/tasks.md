## 1. Dependencies

- [x] 1.1 Add `pyjwt` and `pwdlib[argon2]` to `pyproject.toml` with exact version pins (`uv add "pyjwt==X.Y.Z" "pwdlib[argon2]==X.Y.Z"`)
- [x] 1.2 Run `uv sync` and confirm `uv.lock` is updated; review the dependency diff before proceeding

## 2. Security primitives and configuration

- [x] 2.1 Create `core/security.py` with `hash_password` and `verify_password` using `pwdlib` (Argon2)
- [x] 2.2 Add `generate_password` to `core/security.py` using the standard-library `secrets` module
- [x] 2.3 Add `encode_token` and `decode_token` to `core/security.py` (HS256; payload `sub`, `role`, `exp`); `decode_token` rejects bad signature and expired tokens
- [x] 2.4 Add JWT secret, algorithm, and access-token expiry settings to `config.py`, sourced from the environment, with no insecure production default for the secret
- [x] 2.5 Document the new settings in `.env` and `.env.example`
- [x] 2.6 Confirm `core/security.py` imports nothing from any slice (leaf module preserved)

## 3. User slice — domain and infrastructure

- [x] 3.1 Create `users/domain/user_model.py`: `UserRole` `StrEnum` (`admin`/`staff`/`member`), the `User` table entity (`email`, `password_hash`, `role`, `is_active`) with the named `uq_users_email` constraint, email validation/normalization, and the `UserPublic` schema (no `password_hash`)
- [x] 3.2 Create `users/domain/user_repository.py`: `UserRepository` ABC (`get_by_email`, `get_by_id`, `create`)
- [x] 3.3 Create `users/domain/user_exceptions.py`: email-collision and credential/inactive errors
- [x] 3.4 Create `users/infrastructure/sql_user_repository.py`: `SqlModelUserRepository` implementing the ABC, mapping the `uq_users_email` violation to the email-collision error
- [x] 3.5 Create `users/application/auth_service.py`: `AuthService` that authenticates an email/password pair (verifying the hash and `is_active`) and issues an access token

## 4. Authentication endpoints and the auth gate

- [x] 4.1 Add the `get_current_user` dependency in the `users/` slice: decode the bearer token, load the `User`, reject missing/invalid/expired tokens and inactive users with `401`
- [x] 4.2 Create `users/infrastructure/auth_router.py` with `POST /auth/login` (`OAuth2PasswordRequestForm`, returns `access_token` + `token_type`) — public
- [x] 4.3 Add `GET /auth/me` to the auth router, returning `UserPublic` for the authenticated user
- [x] 4.4 Register the auth router in `main.py` without the auth gate
- [x] 4.5 In `main.py`, attach `dependencies=[Depends(get_current_user)]` to the `books`, `book_copies`, `members`, and `loans` routers at `include_router`; keep `/health` public

## 5. Member account provisioning

- [x] 5.1 Update `members/domain/member_model.py`: drop the `email` column and `uq_members_email`, add the required unique `user_id` FK to `users.id`
- [x] 5.2 Update the member schemas: `MemberCreate` = `full_name`/`email`/`status?` (email validated per the `User` rule, no password), `MemberPublic` exposes `email`, add a creation-response schema carrying the one-time `initial_password`
- [x] 5.3 Update `MemberService.create` to provision the account in one operation: generate a password, create the `member`-role `User`, then the linked `Member` — orchestrating `UserRepository` and `MemberRepository`
- [x] 5.4 Update `SqlModelMemberRepository` so list/get expose `email` via a join to `users`, and `email` filter/sort resolve through that join
- [x] 5.5 Update `members/infrastructure/member_router.py`: `POST /members` returns the creation response with `initial_password`; duplicate email yields `409`

## 6. Database migration

- [x] 6.1 Generate an Alembic migration: `CREATE TABLE users` (with `uq_users_email`) and `ALTER TABLE members` to add `user_id` and drop `email` + `uq_members_email`
- [x] 6.2 Verify `make db-migrate` applies cleanly and the downgrade reverses both tables to the prior schema

## 7. Database seeding

- [x] 7.1 Add a `SAMPLE_USERS` block to `scripts/seed.py`: one `admin` and at least two `staff`, hashed passwords, `is_active` true; admin credentials known to the developer (env or fixed dev default)
- [x] 7.2 Update the members seeding block to create each member together with its linked `member`-role `User`
- [x] 7.3 Update the seeding order to users → books → members → book copies → loans, keeping per-entity idempotency
- [x] 7.4 Run `make db-down` (wipe volume) → `make db-up` → `make db-migrate` → `make db-seed` and confirm a clean rebuild

## 8. Tests

- [x] 8.1 Add an authenticated-client fixture to `tests/conftest.py` (overriding `get_current_user`) and a helper to obtain a real token
- [x] 8.2 Update the existing `books`, `book_copies`, `members`, and `loans` tests to authenticate under the new gate
- [x] 8.3 Test `core/security.py` primitives: hashing/verification, password generation, token encode/decode including expired and tampered tokens
- [x] 8.4 Test `POST /auth/login` (success, wrong password, unknown email, inactive user) and `GET /auth/me` (authenticated and unauthenticated)
- [x] 8.5 Test the auth gate: protected endpoints return `401` without a token; `/health` and `/auth/login` stay public
- [x] 8.6 Test member provisioning: `POST /members` creates a linked `member`-role `User`, returns a one-time `initial_password`, and rejects a duplicate email with `409`
- [x] 8.7 Run `make coverage` and confirm coverage stays close to 100%

## 9. Documentation and verification

- [x] 9.1 Update `CLAUDE.md`: the `users/` slice, the `/auth` endpoints, the system-wide auth requirement, and the new environment variables
- [x] 9.2 Run `make check` and `make test`; smoke-test by logging in as the seeded admin and calling `GET /auth/me`
