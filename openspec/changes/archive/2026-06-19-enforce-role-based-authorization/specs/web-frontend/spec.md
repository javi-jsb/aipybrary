## MODIFIED Requirements

### Requirement: Role-aware action visibility

The system SHALL resolve the authenticated user's role (via `GET /auth/me`) and use it to show or hide actions, navigation, and views in the UI so the interface mirrors the backend's enforced permission matrix. This gating is a usability aid only and SHALL NOT be relied upon as an authorization boundary; the backend remains the security boundary. In particular, a `member` SHALL be shown only their own loans, SHALL NOT be shown the members/users listing or its navigation, and SHALL NOT be shown catalog, copy, or loan management controls.

#### Scenario: Actions reflect the user's role

- **WHEN** the authenticated user's role does not correspond to a given action
- **THEN** the UI does not present that action's control

#### Scenario: Member does not see members navigation

- **WHEN** a `member` is authenticated
- **THEN** the members/users navigation entry and routes are not presented

#### Scenario: Member loans view is scoped to self

- **WHEN** a `member` opens the loans view
- **THEN** the application requests and renders only that member's own loans, with no borrow or return controls

## ADDED Requirements

### Requirement: Graceful handling of forbidden responses

The system SHALL handle a `403 Forbidden` response from the API gracefully — presenting a clear "not allowed" message or redirecting — rather than surfacing a raw error or a blank state. This complements role-aware hiding for cases where a forbidden route is reached directly (e.g. via a deep link).

#### Scenario: Forbidden route is handled

- **WHEN** an authenticated request returns `403 Forbidden`
- **THEN** the application shows a clear "not allowed" message or redirects the user, instead of an unhandled error

#### Scenario: Forbidden is distinguished from unauthenticated

- **WHEN** a request returns `401 Unauthorized`
- **THEN** the application treats it as a session/authentication problem (e.g. redirect to login), distinct from the `403` "not allowed" handling
