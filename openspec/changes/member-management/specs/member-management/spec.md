## ADDED Requirements

### Requirement: Member domain model

The application SHALL define a `Member` entity as a SQLModel table class with the following fields:

| Field | Type | Constraints |
|---|---|---|
| `id` | `uuid.UUID` | PK, default UUIDv7 via `uuid_utils.uuid7()` |
| `full_name` | `str` | Required, max 300 chars |
| `email` | `str` | Required, max 320 chars, unique (constraint `uq_members_email`), valid format, normalized |
| `status` | `MemberStatus` | Required, enum `active` / `suspended`, default `active` |
| `created_at` | `datetime` | Server-default `now()`, not client-updatable |
| `updated_at` | `datetime` | Server-default `now()`, auto-updated on modification |

`MemberStatus` SHALL be a `StrEnum` with members `active` and `suspended`, mirroring the `StrEnum` pattern used by the `books` slice.

The model SHALL also define separate Pydantic schemas for API boundaries: `MemberCreate`, `MemberUpdate`, and `MemberPublic`, plus a `MemberListResponse` paginated envelope consistent with `BookListResponse` (`items`, `total`, `page`, `size`, and a computed `pages`).

#### Scenario: Member is created with required fields

- **WHEN** a Member is instantiated with `full_name` and `email`
- **THEN** it receives a UUIDv7 `id`, `status` defaults to `active`, and `created_at` and `updated_at` are set automatically

#### Scenario: Email uniqueness is enforced

- **WHEN** two members are created with the same `email`
- **THEN** the database rejects the second insert with a unique constraint violation

#### Scenario: Status defaults to active

- **WHEN** a Member is created without an explicit `status`
- **THEN** its `status` is `active`

### Requirement: Email validation and normalization

`MemberCreate` and `MemberUpdate` SHALL validate and normalize the `email`
field at the schema boundary, mirroring the `isbn` validator pattern in the
`books` slice: the value is trimmed and lowercased, then rejected if it does
not match a basic `local@domain.tld` shape (no whitespace, exactly one `@`, a
dotted domain). A `None` email on `MemberUpdate` bypasses validation.

Because the value is lowercased before persistence, the `email` uniqueness
constraint is effectively case-insensitive.

#### Scenario: Invalid email rejected

- **WHEN** a client sends `POST /members` or `PATCH /members/{member_id}` with an `email` that is not a valid address (e.g. `not-an-email`)
- **THEN** the response status code is `422`

#### Scenario: Email is normalized

- **WHEN** a client sends `POST /members` with `email` `"  Ada@Example.COM  "`
- **THEN** the created member's `email` is `ada@example.com`

#### Scenario: Duplicate email is detected case-insensitively

- **WHEN** a member with `email` `case@example.com` exists
- **AND** a client sends `POST /members` with `email` `CASE@example.com`
- **THEN** the response status code is `409`

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

The API SHALL expose `POST /members` that creates a new member from a `MemberCreate` payload. `MemberCreate` SHALL accept `full_name`, `email`, and an optional `status` (defaulting to `active`).

#### Scenario: Valid creation

- **WHEN** a client sends `POST /members` with a valid JSON body containing `full_name` and `email`
- **THEN** the response status code is `201`
- **AND** the response body is the created `MemberPublic` object with a generated `id` and `status` `active`

#### Scenario: Missing required fields

- **WHEN** a client sends `POST /members` without `full_name` or `email`
- **THEN** the response status code is `422` with validation error details

#### Scenario: Duplicate email rejected

- **WHEN** a client sends `POST /members` with an `email` that already exists
- **THEN** the response status code is `409`

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

#### Scenario: Member exists

- **WHEN** a client sends `DELETE /members/{member_id}` with a valid existing ID
- **THEN** the response status code is `204`
- **AND** the member is no longer retrievable via `GET /members/{member_id}`

#### Scenario: Member does not exist

- **WHEN** a client sends `DELETE /members/{member_id}` with a non-existent ID
- **THEN** the response status code is `404`

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

The members table SHALL be created and managed via an Alembic migration, not via `SQLModel.metadata.create_all()`. The migration SHALL include the unique constraint on `email`, explicitly named `uq_members_email` so the SQL repository can distinguish an email collision from any other integrity violation.

#### Scenario: Migration creates the table

- **WHEN** a developer runs `alembic upgrade head` on a database without the `members` table
- **THEN** the `members` table exists with all columns matching the `Member` model and a unique constraint on `email`

#### Scenario: Migration is reversible

- **WHEN** a developer downgrades the members revision after applying it
- **THEN** the `members` table is dropped
- **AND** re-applying the members revision recreates it
