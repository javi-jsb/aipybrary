# Member Management

## Purpose

Provide CRUD operations for the Member entity — library patrons who can borrow books. This includes the domain model and its 1:1 link to a `User` (which owns the member's email — see the `authentication` capability), repository abstraction, application service, paginated/filterable/sortable HTTP endpoints, the member lifecycle status, and the database migration for the members table.

## Requirements

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

### Requirement: Member repository abstraction

The domain SHALL define a `MemberRepository` ABC that declares the contract for member persistence operations: `create`, `get_by_id`, `get_paginated`, `update`, `delete`.

The infrastructure layer SHALL provide `SqlModelMemberRepository` that inherits from `MemberRepository` and implements all methods using SQLModel async sessions, mirroring `SqlModelBookRepository`.

#### Scenario: Repository contract is enforced

- **WHEN** a class inherits from `MemberRepository` but does not implement all abstract methods
- **THEN** Python raises `TypeError` at instantiation time

### Requirement: Member application service

The application layer SHALL provide a `MemberService` that receives a `MemberRepository` via constructor injection and orchestrates CRUD operations.

The service MUST NOT depend on SQLModel, FastAPI, or any infrastructure detail — only on the domain's `MemberRepository` ABC and model.

#### Scenario: Service creates a member

- **WHEN** `MemberService.create(data)` is called with valid `MemberCreate` data
- **THEN** it delegates to the repository and returns the created `Member`

#### Scenario: Service returns None for missing member

- **WHEN** `MemberService.get_by_id(id)` is called with a non-existent ID
- **THEN** it returns `None`

### Requirement: Paginated member list

The API SHALL expose `GET /members` that returns a paginated `MemberListResponse` envelope (`items`, `total`, `page`, `size`, computed `pages`), mirroring the `/books` list-query contract.

Query parameters:

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `page` | `int` | `1` | `>= 1` |
| `size` | `int` | `20` | `>= 1`, `<= 100` |

#### Scenario: Default pagination on non-empty database

- **WHEN** a client sends `GET /members` with no query parameters
- **AND** the database contains 25 members
- **THEN** the response status code is `200`
- **AND** `items` contains 20 `MemberPublic` objects
- **AND** `total` is `25`, `page` is `1`, `size` is `20`, `pages` is `2`

#### Scenario: Second page

- **WHEN** a client sends `GET /members?page=2&size=20`
- **AND** the database contains 25 members
- **THEN** `items` contains 5 members
- **AND** `page` is `2`

#### Scenario: No members exist

- **WHEN** a client sends `GET /members`
- **AND** the database is empty
- **THEN** the response status code is `200`
- **AND** `items` is `[]`, `total` is `0`, `pages` is `0`

#### Scenario: page out of range

- **WHEN** a client sends `GET /members?page=0`
- **THEN** the response status code is `422`

#### Scenario: size exceeds maximum

- **WHEN** a client sends `GET /members?size=101`
- **THEN** the response status code is `422`

### Requirement: Filter members by full_name, email and status

`GET /members` SHALL accept optional `full_name` and `email` query parameters that filter results using a case-insensitive partial match (SQL `ILIKE`), and an optional `status` query parameter that filters by exact `MemberStatus` value (`active` or `suspended`).

All filters are independent and additive (AND logic when more than one is provided). An invalid `status` value yields `422`.

#### Scenario: Filter by full_name

- **WHEN** a client sends `GET /members?full_name=garcia`
- **AND** the database contains members named "Ana García" and others
- **THEN** only members whose `full_name` contains "garcia" (case-insensitive) are returned
- **AND** `total` reflects only the matching count

#### Scenario: Filter by email

- **WHEN** a client sends `GET /members?email=@example.com`
- **THEN** only members whose `email` contains "@example.com" (case-insensitive) are returned

#### Scenario: Filter by status

- **WHEN** a client sends `GET /members?status=suspended`
- **THEN** only members whose `status` is `suspended` are returned

#### Scenario: Invalid status value

- **WHEN** a client sends `GET /members?status=banned`
- **THEN** the response status code is `422`

#### Scenario: Combined filters

- **WHEN** a client sends `GET /members?full_name=ana&status=suspended`
- **THEN** only members matching BOTH filters are returned

#### Scenario: No matches

- **WHEN** a client sends `GET /members?full_name=zzznomatch`
- **THEN** the response status code is `200`
- **AND** `items` is `[]` and `total` is `0`

### Requirement: Sort member list

`GET /members` SHALL accept `sort_by` and `order` query parameters.

| Parameter | Allowed values | Default |
|---|---|---|
| `sort_by` | `full_name`, `email`, `status`, `created_at` | `created_at` |
| `order` | `asc`, `desc` | `desc` |

#### Scenario: Sort by full_name ascending

- **WHEN** a client sends `GET /members?sort_by=full_name&order=asc`
- **THEN** the response status code is `200`
- **AND** `items` are ordered alphabetically by `full_name`

#### Scenario: Default sort

- **WHEN** a client sends `GET /members` with no sort parameters
- **THEN** members are ordered by `created_at` descending (newest first)

#### Scenario: Invalid sort_by value

- **WHEN** a client sends `GET /members?sort_by=invalid`
- **THEN** the response status code is `422`

### Requirement: Get a member by ID

The API SHALL expose `GET /members/{member_id}` that returns a single member.

#### Scenario: Member exists

- **WHEN** a client sends `GET /members/{member_id}` with a valid existing ID
- **THEN** the response status code is `200`
- **AND** the response body is a JSON `MemberPublic` object

#### Scenario: Member does not exist

- **WHEN** a client sends `GET /members/{member_id}` with a non-existent ID
- **THEN** the response status code is `404`

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

### Requirement: Update a member

The API SHALL expose `PATCH /members/{member_id}` that partially updates an existing member from a `MemberUpdate` payload. `MemberUpdate` SHALL allow updating `full_name`, `email`, and `status`, each optional.

#### Scenario: Valid partial update

- **WHEN** a client sends `PATCH /members/{member_id}` with a subset of fields
- **THEN** the response status code is `200`
- **AND** only the provided fields are updated; other fields remain unchanged
- **AND** the response body is the updated `MemberPublic` object

#### Scenario: Member does not exist

- **WHEN** a client sends `PATCH /members/{member_id}` with a non-existent ID
- **THEN** the response status code is `404`

#### Scenario: Update to a duplicate email rejected

- **WHEN** a client sends `PATCH /members/{member_id}` setting `email` to a value already used by another member
- **THEN** the response status code is `409`

### Requirement: Delete a member

The API SHALL expose `DELETE /members/{member_id}` that removes a member.

A member that is still referenced by a `Loan` SHALL NOT be deletable: the `loans.member_id` foreign key is `ON DELETE RESTRICT`. The SQL repository SHALL catch the resulting `IntegrityError`, recognise the `fk_loans_member_id_members` constraint via `is_constraint_violated`, and translate it into a `MemberHasLoansError` domain exception, mirroring the `BookHasCopiesError` pattern. The router SHALL map that exception to `409 Conflict`. The constraint name SHALL be exposed as `MEMBER_FK_CONSTRAINT` in `app.loans.domain.loan_model` so the member repository can reference it without hardcoding the string (an infrastructure-to-domain cross-slice import, which is acceptable; the constraint is that domain layers do not import from other slices).

#### Scenario: Member exists

- **WHEN** a client sends `DELETE /members/{member_id}` with a valid existing ID
- **THEN** the response status code is `204`
- **AND** the member is no longer retrievable via `GET /members/{member_id}`

#### Scenario: Member does not exist

- **WHEN** a client sends `DELETE /members/{member_id}` with a non-existent ID
- **THEN** the response status code is `404`

#### Scenario: Member has loans

- **WHEN** a client sends `DELETE /members/{member_id}` for a member that is still referenced by at least one `Loan`
- **THEN** the response status code is `409`
- **AND** the member is still retrievable via `GET /members/{member_id}`

### Requirement: Member lifecycle status

The `Member` entity SHALL carry a `status` field with values `active` or `suspended`, defaulting to `active`. In this phase the status has no behavioural side effects; it exists so that the `lending` capability (Phase 3) can forbid suspended members from borrowing.

#### Scenario: Member can be suspended

- **WHEN** a client sends `PATCH /members/{member_id}` with `status` set to `suspended`
- **THEN** the response status code is `200`
- **AND** the returned `MemberPublic` has `status` `suspended`

#### Scenario: Invalid status rejected

- **WHEN** a client sends `POST /members` or `PATCH /members/{member_id}` with a `status` value other than `active` or `suspended`
- **THEN** the response status code is `422`

### Requirement: Members table migration

The `members` table SHALL be created and managed via Alembic migrations, not via `SQLModel.metadata.create_all()`. After the `authentication` change the `members` table SHALL have a `user_id` column — a `NOT NULL`, `UNIQUE` foreign key to `users.id` — and SHALL NOT have an `email` column or the `uq_members_email` constraint; a member's email is an attribute of the linked `User`.

#### Scenario: Migration applies the members schema

- **WHEN** a developer runs `alembic upgrade head`
- **THEN** the `members` table exists with columns matching the `Member` model, including a `NOT NULL` unique `user_id` foreign key to `users.id`, and no `email` column

#### Scenario: Migration is reversible

- **WHEN** a developer downgrades the `authentication` revision after applying it
- **THEN** the `members` table returns to its previous schema — with `email` and without `user_id`
- **AND** re-applying the revision reapplies the new schema
