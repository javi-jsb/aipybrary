# authorization Specification

## Purpose

Define the server-side, role-based access-control boundary for the API. Authentication proves *identity*; authorization enforces *what each role may do*. This capability owns the reusable `require_role` / member-ownership dependencies layered on the authenticated-user dependency, the per-endpoint permission matrix (admin/staff/member) across books, book copies, members, and loans, member self-scoping for profile and loan reads, and the `403 Forbidden` (authenticated-but-unauthorized) vs `401 Unauthorized` (missing/invalid token) distinction. The backend is the security boundary; the frontend mirror is not trusted.

## Requirements
### Requirement: Role-based authorization dependency

The system SHALL provide a reusable authorization dependency, layered on the authenticated-user dependency, that admits a request only when the caller's role is in an allowed set and otherwise rejects it with `403 Forbidden`. The rejection MUST be distinct from the `401 Unauthorized` raised for missing or invalid authentication.

#### Scenario: Allowed role passes
- **WHEN** an authenticated `staff` user calls an endpoint guarded for `admin`/`staff`
- **THEN** the request proceeds and the caller's `User` is available to the handler

#### Scenario: Disallowed role is forbidden
- **WHEN** an authenticated `member` calls an endpoint guarded for `admin`/`staff`
- **THEN** the response is `403 Forbidden`

#### Scenario: Unauthenticated request is unauthorized, not forbidden
- **WHEN** a request without a valid token reaches a role-guarded endpoint
- **THEN** the response is `401 Unauthorized`, not `403`

### Requirement: Books and copies authorization

Reading books and book copies SHALL be allowed for any authenticated user. Creating, updating, or deleting books or book copies SHALL be restricted to `admin` and `staff`.

#### Scenario: Member reads the catalog
- **WHEN** a `member` lists or retrieves books or book copies
- **THEN** the request succeeds

#### Scenario: Member cannot mutate the catalog
- **WHEN** a `member` attempts to create, update, or delete a book or a book copy
- **THEN** the response is `403 Forbidden`

#### Scenario: Staff manages the catalog
- **WHEN** a `staff` user creates, updates, or deletes a book or a book copy
- **THEN** the request succeeds

### Requirement: Member listing and management authorization

Listing members and creating, updating, or deleting members SHALL be restricted to `admin` and `staff`. A `member` SHALL be able to read only their own member profile and SHALL NOT list members or read another member's profile.

#### Scenario: Staff lists and manages members
- **WHEN** a `staff` user lists members or creates, updates, or deletes a member
- **THEN** the request succeeds

#### Scenario: Member cannot list members
- **WHEN** a `member` calls the member listing endpoint
- **THEN** the response is `403 Forbidden`

#### Scenario: Member reads own profile
- **WHEN** a `member` retrieves the member resource linked to their own user
- **THEN** the request succeeds and returns their profile

#### Scenario: Member cannot read another member's profile
- **WHEN** a `member` retrieves a member resource that is not their own
- **THEN** the response is `403 Forbidden`

### Requirement: Loan authorization and member scoping

Borrowing, returning, undoing a return, and cancelling loans SHALL be restricted to `admin` and `staff`. Listing loans SHALL return all loans for `admin`/`staff`, while for a `member` it SHALL be scoped to loans whose `member_id` is the caller's own member, regardless of any supplied filter. A `member` retrieving an individual loan that is not their own SHALL be rejected with `403 Forbidden`.

#### Scenario: Member loan list is scoped to self
- **WHEN** a `member` lists loans, with or without a `member_id` filter
- **THEN** the response contains only loans belonging to the caller's own member

#### Scenario: Member cannot borrow, return, or cancel
- **WHEN** a `member` attempts to borrow, return, undo a return, or cancel a loan
- **THEN** the response is `403 Forbidden`

#### Scenario: Staff borrows and returns
- **WHEN** a `staff` user borrows or returns a loan
- **THEN** the request succeeds

#### Scenario: Member cannot read another member's loan
- **WHEN** a `member` retrieves a loan that does not belong to their own member
- **THEN** the response is `403 Forbidden`

### Requirement: Member identity resolution

The system SHALL resolve a `member`-role user to their linked member record so ownership-based authorization can be evaluated. Resolution SHALL be by the user's id against the member's `user_id`.

#### Scenario: Member user resolves to their member record
- **WHEN** the authorization layer resolves a `member`-role user
- **THEN** it returns the member whose `user_id` equals that user's id

#### Scenario: No linked member yields no ownership
- **WHEN** the authorization layer resolves a user that has no linked member record
- **THEN** ownership-scoped access is denied with `403 Forbidden`

### Requirement: Frontend is not a trust boundary

Authorization SHALL be enforced on the backend independently of the frontend. The system MUST reject an unauthorized request even when it is crafted directly against the API, bypassing any frontend control hiding.

#### Scenario: Direct API call bypassing the UI is still enforced
- **WHEN** a `member` sends a write request directly to a staff-only endpoint without going through the SPA
- **THEN** the response is `403 Forbidden`
