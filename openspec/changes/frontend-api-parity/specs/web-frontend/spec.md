## ADDED Requirements

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

The system SHALL let an authenticated user list members, view a member's detail, create a member, and update a member, through the corresponding member endpoints.

#### Scenario: List and view members

- **WHEN** the user opens the members view
- **THEN** the application requests the members list and renders the returned members, with navigation to each member's detail

#### Scenario: Create member surfaces the one-time initial password

- **WHEN** the user creates a member successfully
- **THEN** the application displays the one-time `initial_password` returned by `POST /members` exactly once and does not show it on subsequent reads

#### Scenario: Update member

- **WHEN** the user saves changes to a member
- **THEN** the application sends the update request and reflects the updated member on success

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
