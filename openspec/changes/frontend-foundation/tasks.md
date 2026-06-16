## 1. Scaffold the frontend project

- [x] 1.1 Create `/frontend` with a Vite + React + TypeScript app, managed by pnpm
- [x] 1.2 Add and configure Tailwind (config + base stylesheet wired into the app entry)
- [x] 1.3 Add eslint + prettier configuration consistent with a TS React project
- [x] 1.4 Add a `.gitignore` entry for `frontend/node_modules` (and Vite build output)
- [x] 1.5 Add `VITE_API_BASE_URL` support (`.env.example` documenting it, default `http://localhost:8000`)
- [x] 1.6 Verify `pnpm dev` serves the app locally with HMR

## 2. API client layer

- [x] 2.1 Implement the `apiClient` helper: prepend base URL, attach `Authorization: Bearer <token>` when a token is present, parse JSON, throw on non-success
- [x] 2.2 Add hand-written TypeScript types for `Book` and the auth login request/response payloads
- [x] 2.3 Add typed call functions for `POST /auth/login` and `GET /books` built on `apiClient`

## 3. Authentication

- [x] 3.1 Add token + authenticated-state handling (store on login, read by `apiClient`, behind a single seam)
- [x] 3.2 Build the login screen: OAuth2 form credentials submitted to `POST /auth/login`
- [x] 3.3 On success, store the `access_token` and transition to the authenticated view
- [x] 3.4 On failure, show an error and remain on the login screen with no token stored

## 4. Protected Books list

- [x] 4.1 Add routing/gating so the Books view is reachable only when authenticated; otherwise show login
- [x] 4.2 Build the Books list view: fetch `GET /books` with the bearer token and render the results
- [x] 4.3 Handle loading and error states for the books request

## 5. Documentation

- [x] 5.1 Update root `CLAUDE.md` with a frontend section: stack, `/frontend` layout, and commands
- [x] 5.2 Add a short `frontend/README.md` covering setup and the `VITE_API_BASE_URL` requirement

## 6. Verification

- [x] 6.1 With the backend running (CORS enabled) and seeded data, log in through the UI and confirm a token is stored
- [x] 6.2 Confirm the Books list renders real data from `GET /books`, and that error/unauthenticated paths behave per the spec scenarios
