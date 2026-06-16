## Why

Exercising the API today relies on FastAPI's `/docs`, which is increasingly tedious for manually probing flows. A minimal web UI would make it faster to visualize and test API changes — and doubles as a hands-on way to learn React, TypeScript, and Tailwind alongside the backend work.

## What Changes

- Introduce a new self-contained `/frontend` directory at the repo root. The backend stays exactly where it is (Option A — no backend files move).
- Scaffold a React + TypeScript + Tailwind single-page app built with Vite and managed with pnpm, including eslint/prettier and a gitignore entry for `node_modules`.
- Add a small `apiClient` fetch wrapper (configurable base URL, `Authorization: Bearer` header, JSON parsing and error handling) plus hand-written TypeScript types for `Book` and auth payloads.
- Add a login screen that posts OAuth2 form credentials to `POST /auth/login`, stores the returned `access_token`, and reflects authenticated state.
- Add one protected screen: a Books list rendering real data from `GET /books` using the stored token.
- Update root `CLAUDE.md` with a frontend section (stack, layout, commands).
- The frontend calls the backend directly cross-origin at `http://localhost:8077`. This assumes CORS is already enabled on the API (handled by a separate backend change done before frontend implementation). No Vite dev proxy is used.

Out of scope (future changes): members/copies/loans screens, create/borrow/return actions, OpenAPI-generated types, TanStack Query, a dedicated frontend CI job, and production deployment/CORS hardening.

## Capabilities

### New Capabilities
- `web-frontend`: A browser-based UI that authenticates against the API and renders protected resource views — initially login plus a Books list — through a shared fetch-based API client.

### Modified Capabilities
<!-- None. The frontend is purely additive; backend CORS is handled by a separate change. -->

## Impact

- **New code**: `/frontend` directory (Vite + React + TS + Tailwind app, pnpm-managed).
- **New dependencies**: Node.js toolchain (pnpm, Vite, React, TypeScript, Tailwind, eslint/prettier) — isolated to `/frontend`, independent of the Python `pyproject.toml`.
- **Docs**: root `CLAUDE.md` gains a frontend section.
- **Backend**: untouched by this change. Depends on a separate backend change enabling CORS for the dev origin before this frontend is implemented.
- **Runtime assumption**: the API is reachable at `http://localhost:8077` with CORS enabled; the frontend base URL is configurable via a Vite env var (`VITE_API_BASE_URL`).
