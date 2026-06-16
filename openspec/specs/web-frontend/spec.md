# web-frontend Specification

## Purpose

Provide a browser-based single-page application (React + TypeScript + Tailwind via Vite) that authenticates against the API and renders protected resource views through a shared, fetch-based `apiClient` seam. The initial scope is the foundation: a configurable API base URL, the shared client (bearer token + JSON + error surfacing), user login with token storage, and a protected Books list — the vertical slice that proves end-to-end auth and data rendering.

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

