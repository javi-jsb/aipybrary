# web-frontend Specification

## Purpose

Provide a browser-based single-page application (React + TypeScript + Tailwind via Vite) that authenticates against the API and renders protected resource views through a shared, fetch-based `apiClient` seam. Built on the foundation (a configurable API base URL, the shared client with bearer token + JSON + error surfacing, user login with token storage, and a protected Books list), the application now reaches parity with the API surface: client-side routing behind an authenticated layout, role-aware action visibility, full Books CRUD, member management, book-copy management, loan borrow/return, and consistent client- and server-side form error handling.

## Requirements
### Requirement: Frontend application shell

The system SHALL provide a browser-based single-page application, built with React, TypeScript, and Tailwind via Vite, served independently from the backend during development.

#### Scenario: Development server starts

- **WHEN** a developer runs the frontend dev command from `/frontend`
- **THEN** Vite serves the application locally with hot module replacement enabled

#### Scenario: API base URL is configurable

- **WHEN** the application issues a request to the backend
- **THEN** it targets the base URL from the `VITE_API_BASE_URL` environment variable, defaulting to `http://localhost:8077` when unset

### Requirement: Shared API client

The system SHALL route all backend requests through a single `apiClient` helper that prepends the configured base URL, attaches the stored access token as an `Authorization: Bearer <token>` header when present, parses JSON responses, and surfaces non-success responses as errors.

#### Scenario: Authenticated request attaches bearer token

- **WHEN** an access token is stored and a request is made through `apiClient`
- **THEN** the request includes an `Authorization: Bearer <token>` header

#### Scenario: Request without a stored token omits the header

- **WHEN** no access token is stored and a request is made through `apiClient`
- **THEN** the request is sent without an `Authorization` header

#### Scenario: Error response is surfaced

- **WHEN** the backend responds with a non-success status code
- **THEN** `apiClient` raises an error rather than returning the response body as data

### Requirement: User login

The system SHALL provide a login screen that submits OAuth2 form credentials to `POST /auth/login` and, on success, stores the returned `access_token` and transitions the application to an authenticated state.

#### Scenario: Successful login

- **WHEN** a user submits valid credentials on the login screen
- **THEN** the application stores the returned `access_token` and shows the authenticated view

#### Scenario: Failed login

- **WHEN** a user submits invalid credentials
- **THEN** the application shows an error message and remains on the login screen with no token stored

### Requirement: Protected Books list

The system SHALL render a Books list, retrieved from `GET /books` using the stored access token, only to an authenticated user.

#### Scenario: Authenticated user views books

- **WHEN** an authenticated user opens the Books view
- **THEN** the application requests `GET /books` with the bearer token and renders the returned books

#### Scenario: Unauthenticated access is prevented

- **WHEN** a user who is not authenticated attempts to reach the Books view
- **THEN** the application shows the login screen instead of issuing the request

#### Scenario: Books request fails

- **WHEN** the `GET /books` request returns an error
- **THEN** the application shows an error state rather than a partial or empty list presented as success

### Requirement: Client-side routing and authenticated layout

The system SHALL provide client-side routing that maps URLs to views, served behind a shared authenticated layout (persistent navigation and sign-out) for all protected resources, and SHALL redirect unauthenticated access to the login route.

#### Scenario: Authenticated navigation updates the URL

- **WHEN** an authenticated user navigates to a resource view (e.g. the members list)
- **THEN** the browser URL reflects that view and the view renders within the authenticated layout without a full page reload

#### Scenario: Deep link while authenticated

- **WHEN** an authenticated user reloads or opens a deep link to a resource URL (e.g. a book detail with an id)
- **THEN** the application renders that view directly rather than resetting to a default screen

#### Scenario: Unauthenticated access is redirected

- **WHEN** a user who is not authenticated requests a protected route
- **THEN** the application shows the login route and does not issue the protected request

### Requirement: Role-aware action visibility

The system SHALL resolve the authenticated user's role (via `GET /auth/me`) and use it to show or hide actions in the UI. This gating is a usability aid only and SHALL NOT be relied upon as an authorization boundary.

#### Scenario: Actions reflect the user's role

- **WHEN** the authenticated user's role does not correspond to a given action
- **THEN** the UI does not present that action's control

### Requirement: Book creation

The system SHALL let an authenticated user create a book by submitting its fields to `POST /books`, and on success reflect the new book in the books list.

#### Scenario: Successful creation

- **WHEN** the user submits a valid new book
- **THEN** the application sends `POST /books` and, on success, shows the created book in the list

#### Scenario: Duplicate ISBN rejected

- **WHEN** the create request fails with a conflict (duplicate ISBN)
- **THEN** the application shows the backend error message on the form and does not add a book to the list

### Requirement: Book editing

The system SHALL let an authenticated user edit an existing book via `PATCH /books/{id}` and reflect the updated values after success.

#### Scenario: Successful edit

- **WHEN** the user saves changes to an existing book
- **THEN** the application sends `PATCH /books/{id}` and shows the updated values on success

### Requirement: Book deletion

The system SHALL let an authenticated user delete a book via `DELETE /books/{id}` and remove it from the list on success.

#### Scenario: Successful deletion

- **WHEN** the user confirms deletion of a book
- **THEN** the application sends `DELETE /books/{id}` and removes it from the list on success

#### Scenario: Deletion blocked by existing copies

- **WHEN** the delete request fails because the book has copies
- **THEN** the application shows the backend error message and keeps the book in the list

### Requirement: Member management

The system SHALL let an authenticated user list members, view a member's detail, create a member, update a member, and delete a member, through the corresponding member endpoints. The delete action SHALL be presented only to users whose role permits it (admins).

#### Scenario: List and view members

- **WHEN** the user opens the members view
- **THEN** the application requests the members list and renders the returned members, with navigation to each member's detail

#### Scenario: Create member surfaces the one-time initial password

- **WHEN** the user creates a member successfully
- **THEN** the application displays the one-time `initial_password` returned by `POST /members` exactly once and does not show it on subsequent reads

#### Scenario: Update member

- **WHEN** the user saves changes to a member
- **THEN** the application sends the update request and reflects the updated member on success

#### Scenario: Delete member

- **WHEN** an admin confirms deletion of a member
- **THEN** the application sends `DELETE /members/{id}` and removes the member from the list on success

#### Scenario: Deletion blocked by existing loans

- **WHEN** the delete request fails because the member has loans
- **THEN** the application shows the backend error message and keeps the member in the list

### Requirement: Book-copy management

The system SHALL let an authenticated user view the copies of a book and add or remove copies through the corresponding book-copy endpoints.

#### Scenario: List copies of a book

- **WHEN** the user opens a book's copies view
- **THEN** the application requests and renders that book's copies

#### Scenario: Add a copy

- **WHEN** the user adds a copy to a book
- **THEN** the application sends the create-copy request and shows the new copy on success

#### Scenario: Remove a copy

- **WHEN** the user removes a copy
- **THEN** the application sends the delete-copy request and removes it from the view on success

### Requirement: Loan borrow and return

The system SHALL let an authenticated user list loans, create a loan (borrow), and return a loan, through the corresponding loan endpoints.

#### Scenario: List loans

- **WHEN** the user opens the loans view
- **THEN** the application requests and renders the loans

#### Scenario: Borrow

- **WHEN** the user creates a loan for an available copy and a member
- **THEN** the application sends the borrow request and reflects the new loan on success

#### Scenario: Return

- **WHEN** the user returns an active loan
- **THEN** the application sends the return request and reflects the loan as returned on success

#### Scenario: Borrow rejected by a business rule

- **WHEN** a borrow request fails (e.g. no available copy or the member's active-loan limit is reached)
- **THEN** the application shows the backend error message and does not add a loan

### Requirement: Consistent form error handling

The system SHALL surface backend error responses on the originating form, presenting the response `detail` for validation (`422`) and conflict (`409`) errors, using the shared `apiClient`/`ApiError` seam.

#### Scenario: Validation error is shown on the form

- **WHEN** a create or update submission is rejected by the backend with a validation or conflict error
- **THEN** the application shows the returned error message on the form and preserves the user's input

### Requirement: Client-side form validation

The system SHALL validate form input against the backend's known field constraints before submitting, and SHALL NOT issue the request when the input is invalid — presenting per-field messages instead. This avoids predictable `422` responses. Conflicts that are not knowable on the client (e.g. a duplicate ISBN, `409`) are still surfaced from the server response per the *Consistent form error handling* requirement.

#### Scenario: Invalid input is rejected before submission

- **WHEN** a form field violates a known backend constraint (e.g. a malformed ISBN or a non-integer publication year)
- **THEN** the application shows a field-level error, preserves the input, and does not send the request

#### Scenario: Corrected input is submitted

- **WHEN** the user corrects the invalid field and resubmits
- **THEN** the field error clears and the application sends the request

