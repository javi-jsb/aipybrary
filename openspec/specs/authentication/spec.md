# Authentication

## Purpose

Establish user identity and access control for the API: a `User` entity that owns credentials and role, password hashing and random password generation, JWT access tokens, the login and current-user endpoints, the dependency that resolves a request to its authenticated user, and the central gate that requires a valid bearer token on every endpoint except the public ones. This capability does not enforce roles — any authenticated user may reach any endpoint; role-based restrictions belong to a future `authorization` capability.

## Requirements

### Requirement: User domain model

The application SHALL define a `User` entity as a SQLModel table class with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | PK, default UUIDv7 via `uuid_utils.uuid7()` |
| `email` | `str` | Required, max 320 chars, unique (constraint `uq_users_email`), valid format, normalized |
| `password_hash` | `str` | Required, an Argon2 hash — never a plaintext password |
| `role` | `UserRole` | Required, enum `admin` / `staff` / `member` |
| `is_active` | `bool` | Required, default `true` |
| `created_at` | `datetime` | Server-default `now()`, not client-updatable |
| `updated_at` | `datetime` | Server-default `now()`, auto-updated on modification |

`UserRole` SHALL be a `StrEnum` with members `admin`, `staff`, and `member`, mirroring the `StrEnum` pattern used by `MemberStatus` and `LoanStatus`.

The model SHALL define a `UserPublic` schema for API boundaries that exposes `id`, `email`, `role`, `is_active`, `created_at`, and `updated_at` — and SHALL NOT expose `password_hash`.

#### Scenario: User is created with defaults

- **WHEN** a `User` is instantiated with `email`, `password_hash`, and `role`
- **THEN** it receives a UUIDv7 `id`, `is_active` defaults to `true`, and `created_at` and `updated_at` are set automatically

#### Scenario: Email uniqueness is enforced

- **WHEN** two users are created with the same `email`
- **THEN** the database rejects the second insert with a unique constraint violation

#### Scenario: password_hash is never exposed

- **WHEN** a `User` is serialized through `UserPublic`
- **THEN** the result contains no `password_hash` field

### Requirement: Email validation and normalization

User `email` SHALL be validated and normalized at the schema boundary: the value is trimmed and lowercased, then rejected if it does not match a basic `local@domain.tld` shape (no whitespace, exactly one `@`, a dotted domain). Schemas that accept an email as input — including `MemberCreate` and `MemberUpdate` — SHALL apply this rule; a `None` email on a partial-update schema bypasses validation.

Because the value is lowercased before persistence, the `email` uniqueness constraint on `users` is effectively case-insensitive.

#### Scenario: Invalid email rejected

- **WHEN** a client submits an email that is not a valid address (e.g. `not-an-email`) to an endpoint that creates or updates an account
- **THEN** the response status code is `422`

#### Scenario: Email is normalized

- **WHEN** a client submits the email `"  Ada@Example.COM  "`
- **THEN** the stored email is `ada@example.com`

#### Scenario: Duplicate email detected case-insensitively

- **WHEN** a user with email `case@example.com` exists
- **AND** a client submits `CASE@example.com` for a new account
- **THEN** the response status code is `409`

### Requirement: Password hashing

The system SHALL store passwords only as Argon2 hashes, produced by a `hash_password` primitive in `core/security.py`. A plaintext password SHALL never be persisted or written to logs. A `verify_password` primitive SHALL check a candidate plaintext against a stored hash.

#### Scenario: Password is stored hashed

- **WHEN** a user account is created from a plaintext password
- **THEN** the persisted `password_hash` is an Argon2 hash and differs from the plaintext

#### Scenario: Correct password verifies

- **WHEN** `verify_password` is called with the original plaintext and the stored hash
- **THEN** it returns `true`

#### Scenario: Wrong password fails verification

- **WHEN** `verify_password` is called with an incorrect plaintext and the stored hash
- **THEN** it returns `false`

### Requirement: Random password generation

`core/security.py` SHALL provide a `generate_password` primitive that produces a strong random password using the standard-library `secrets` module. It is used to provision member accounts whose initial password is system-generated.

#### Scenario: Generated password is random

- **WHEN** `generate_password` is called twice
- **THEN** it returns two different values, each non-empty

### Requirement: JWT access token

Login SHALL issue a signed JWT access token using the HS256 algorithm. The token payload SHALL include `sub` (the user's id), a `role` claim, and an expiry (`exp`). A `decode_token` primitive SHALL reject a token whose signature is invalid or whose expiry has passed.

#### Scenario: Token carries subject and role

- **WHEN** a token is issued for a user and then decoded
- **THEN** the decoded payload's `sub` is the user's id and `role` is the user's role

#### Scenario: Expired token is rejected

- **WHEN** `decode_token` is called with a token whose `exp` is in the past
- **THEN** decoding fails

#### Scenario: Tampered token is rejected

- **WHEN** `decode_token` is called with a token whose signature does not match the secret
- **THEN** decoding fails

### Requirement: Login endpoint

The API SHALL expose `POST /auth/login` that accepts an OAuth2 password form (`username` carrying the email, `password`) and returns a JSON body with `access_token` and `token_type` `"bearer"`. The endpoint SHALL be public — reachable without a token.

The submitted email SHALL be trimmed and lowercased before the user lookup so it matches the normalized form stored on `users`; a differently-cased email authenticates the same account.

Authentication SHALL fail with `401 Unauthorized` when the email is unknown, the password does not match, or the user's `is_active` is `false`. An unknown email and a wrong password SHALL be indistinguishable — same response body and equivalent response time, since a hash verification runs even when no user is found — so registered emails cannot be enumerated.

#### Scenario: Successful login

- **WHEN** a client sends `POST /auth/login` with a known email and the correct password for an active user
- **THEN** the response status code is `200`
- **AND** the body contains an `access_token` and `token_type` `"bearer"`

#### Scenario: Wrong password rejected

- **WHEN** a client sends `POST /auth/login` with a known email and an incorrect password
- **THEN** the response status code is `401`

#### Scenario: Unknown email rejected

- **WHEN** a client sends `POST /auth/login` with an email that no user has
- **THEN** the response status code is `401`

#### Scenario: Inactive user rejected

- **WHEN** a client sends `POST /auth/login` with valid credentials for a user whose `is_active` is `false`
- **THEN** the response status code is `401`

#### Scenario: Login is case-insensitive on the email

- **WHEN** a user is registered with the email `case@example.com`
- **AND** a client sends `POST /auth/login` with username `Case@Example.COM` and the correct password
- **THEN** the response status code is `200`

### Requirement: Authenticated user dependency

The `users/` slice SHALL provide a `get_current_user` dependency that extracts the bearer token from the `Authorization` header, decodes it, loads the referenced `User`, and returns it. The dependency SHALL respond `401 Unauthorized` when the header is missing, the token is invalid or expired, the referenced user does not exist, or the user's `is_active` is `false`.

#### Scenario: Valid token resolves to the user

- **WHEN** a request carries a valid, unexpired bearer token for an active user
- **THEN** `get_current_user` returns that `User`

#### Scenario: Missing token rejected

- **WHEN** a request to a protected endpoint carries no `Authorization` header
- **THEN** the response status code is `401`

#### Scenario: Invalid token rejected

- **WHEN** a request carries a malformed or tampered bearer token
- **THEN** the response status code is `401`

### Requirement: Current user endpoint

The API SHALL expose `GET /auth/me` that returns the authenticated user as `UserPublic`.

#### Scenario: Returns the authenticated user

- **WHEN** an authenticated client sends `GET /auth/me`
- **THEN** the response status code is `200`
- **AND** the body is a `UserPublic` object for the token's user, with no `password_hash`

#### Scenario: Unauthenticated request rejected

- **WHEN** a client sends `GET /auth/me` with no token
- **THEN** the response status code is `401`

### Requirement: All endpoints require authentication

Every application HTTP endpoint SHALL reject a request that lacks a valid bearer token with `401 Unauthorized`, except `GET /health` and `POST /auth/login`, which SHALL remain public. Enforcement SHALL be applied centrally at router registration so no endpoint can be left unprotected by omission.

FastAPI's auto-generated documentation endpoints — `/docs`, `/redoc`, and `/openapi.json` — are also reachable without a token. They are framework-provided and mounted on the app instance rather than on a gated router, so the central dependency does not reach them; this is accepted, as they expose only the API schema, not data.

This change does NOT check the user's `role` — any authenticated user may reach any endpoint. Role-based restrictions are introduced by the `authorization` change.

#### Scenario: Protected endpoint without token

- **WHEN** a client sends a request to `GET /books`, `GET /members`, `GET /book-copies`, or `GET /loans` with no token
- **THEN** the response status code is `401`

#### Scenario: Protected endpoint with valid token

- **WHEN** an authenticated client sends a request to a previously open endpoint
- **THEN** the request is not rejected with `401`

#### Scenario: Health check stays public

- **WHEN** a client sends `GET /health` with no token
- **THEN** the response status code is `200`

#### Scenario: Login stays public

- **WHEN** a client sends `POST /auth/login` with no token
- **THEN** the request is not rejected with `401`

### Requirement: Security configuration

`config.py` SHALL expose the JWT secret, the signing algorithm, and the access-token expiry, each sourced from the environment. The JWT secret SHALL NOT have an insecure hardcoded default for non-development use; `.env.example` SHALL document it.

#### Scenario: Settings are sourced from the environment

- **WHEN** the application starts with the JWT settings provided via environment variables
- **THEN** token issuance and verification use those values

### Requirement: Users table migration

The `users` table SHALL be created and managed via an Alembic migration, not via `SQLModel.metadata.create_all()`. The migration SHALL include the unique constraint on `email`, explicitly named `uq_users_email`, so the SQL repository can distinguish an email collision from any other integrity violation. The migration SHALL be reversible.

#### Scenario: Migration creates the table

- **WHEN** a developer runs `alembic upgrade head` on a database without the `users` table
- **THEN** the `users` table exists with all columns matching the `User` model and a unique constraint `uq_users_email` on `email`

#### Scenario: Migration is reversible

- **WHEN** a developer downgrades the authentication revision after applying it
- **THEN** the `users` table is dropped
- **AND** re-applying the revision recreates it
