## MODIFIED Requirements

### Requirement: Member domain model

The application SHALL define a `Member` entity as a SQLModel table class with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | PK, default UUIDv7 via `uuid_utils.uuid7()` |
| `full_name` | `str` | Required, max 300 chars |
| `status` | `MemberStatus` | Required, enum `active` / `suspended`, default `active` |
| `user_id` | `uuid.UUID` | Required, unique, FK to `users.id` |
| `created_at` | `datetime` | Server-default `now()`, not client-updatable |
| `updated_at` | `datetime` | Server-default `now()`, auto-updated on modification |

A `Member` SHALL NOT carry its own `email` column — a member's email is the `email` of its linked `User` (see the `authentication` capability). Every `Member` SHALL be linked 1:1 to exactly one `User` whose `role` is `member`; the `unique` constraint on `user_id` enforces the 1:1 link.

`MemberStatus` SHALL be a `StrEnum` with members `active` and `suspended`, mirroring the `StrEnum` pattern used by the `books` slice.

The model SHALL also define separate Pydantic schemas for API boundaries: `MemberCreate`, `MemberUpdate`, and `MemberPublic`, plus a `MemberListResponse` paginated envelope consistent with `BookListResponse` (`items`, `total`, `page`, `size`, and a computed `pages`). `MemberPublic` SHALL expose the member's `email`, sourced from the linked `User`.

#### Scenario: Member is created with required fields

- **WHEN** a `Member` is created with `full_name` and a linked `User`
- **THEN** it receives a UUIDv7 `id`, `status` defaults to `active`, `user_id` references the linked `User`, and `created_at` and `updated_at` are set automatically

#### Scenario: Member is linked 1:1 to a user

- **WHEN** two members are created referencing the same `user_id`
- **THEN** the database rejects the second insert with a unique constraint violation

#### Scenario: Status defaults to active

- **WHEN** a `Member` is created without an explicit `status`
- **THEN** its `status` is `active`

### Requirement: Create a member

The API SHALL expose `POST /members` that creates a new member from a `MemberCreate` payload. `MemberCreate` SHALL accept `full_name`, `email`, and an optional `status` (defaulting to `active`); it SHALL NOT accept a password.

Because every `Member` is linked 1:1 to a `User`, `POST /members` SHALL — in a single operation — create a `member`-role `User` for the given `email` and a `Member` linked to it. The `email` SHALL be validated and normalized per the `User` email rules (see the `authentication` capability). The system SHALL generate a random initial password for the new `User`, store only its hash, and return the generated plaintext password exactly once in the creation response so it can be relayed to the member.

The creation response SHALL include the created member's public fields and a one-time `initial_password`; the `initial_password` SHALL NOT be retrievable by any subsequent request.

#### Scenario: Valid creation

- **WHEN** a client sends `POST /members` with a valid JSON body containing `full_name` and `email`
- **THEN** the response status code is `201`
- **AND** a `member`-role `User` is created for the `email` and a `Member` linked to it
- **AND** the response body contains the created member (with `status` `active`) and a non-empty one-time `initial_password`

#### Scenario: Missing required fields

- **WHEN** a client sends `POST /members` without `full_name` or `email`
- **THEN** the response status code is `422` with validation error details

#### Scenario: Duplicate email rejected

- **WHEN** a client sends `POST /members` with an `email` already used by an existing `User`
- **THEN** the response status code is `409`
- **AND** no `Member` or `User` is created

### Requirement: Members table migration

The `members` table SHALL be created and managed via Alembic migrations, not via `SQLModel.metadata.create_all()`. After the `authentication` change the `members` table SHALL have a `user_id` column — a `NOT NULL`, `UNIQUE` foreign key to `users.id` — and SHALL NOT have an `email` column or the `uq_members_email` constraint; a member's email is an attribute of the linked `User`.

#### Scenario: Migration applies the members schema

- **WHEN** a developer runs `alembic upgrade head`
- **THEN** the `members` table exists with columns matching the `Member` model, including a `NOT NULL` unique `user_id` foreign key to `users.id`, and no `email` column

#### Scenario: Migration is reversible

- **WHEN** a developer downgrades the `authentication` revision after applying it
- **THEN** the `members` table returns to its previous schema — with `email` and without `user_id`
- **AND** re-applying the revision reapplies the new schema

## REMOVED Requirements

### Requirement: Email validation and normalization

**Reason**: `email` is now an attribute of `User`, not `Member` — see Decision 2 in the change design. The validation and normalization rule moves to the `authentication` capability.

**Migration**: Email validation and normalization for `POST /members` and `PATCH /members` input is governed by the "Email validation and normalization" requirement in the `authentication` spec, which `MemberCreate` and `MemberUpdate` apply at their schema boundary. The `uq_members_email` constraint is replaced by `uq_users_email` on the `users` table.
