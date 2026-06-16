## Context

`aipybrary` is an API-only repository: the root holds the Python backend (`pyproject.toml`, `src/app`, `alembic`, `Makefile`, `openspec`). Manual API testing currently goes through FastAPI's `/docs`, which has become tedious. This change adds a minimal web UI to visualize and exercise the API, while serving as a learning vehicle for React, TypeScript, and Tailwind.

The backend now sits behind a JWT bearer gate: all routes except `GET /health`, `POST /auth/login`, and the docs endpoints require a valid token. The frontend must therefore log in, hold a token, and send it on protected calls.

This is a learning project, so the guiding constraint is simplicity — introduce complexity only when a real need appears.

## Goals / Non-Goals

**Goals:**
- A self-contained `/frontend` SPA that proves an end-to-end vertical slice: login → store token → render a protected Books list.
- A single, obvious seam (`apiClient`) for all backend calls, so future evolution (TanStack Query, generated client) is a localized change.
- Zero disruption to the working backend: the frontend is purely additive.

**Non-Goals:**
- Members/copies/loans screens or any create/borrow/return actions.
- OpenAPI-generated types, TanStack Query, a dedicated frontend CI job.
- Production deployment, build/serve integration, or CORS hardening.
- Restructuring the repo into symmetric `/backend` + `/frontend` (deferred; promote later only if the asymmetry creates real friction).

## Decisions

### Repo layout — root stays backend, add `/frontend` (Option A)
Keep the backend at the repo root and add a single self-contained `/frontend` directory with its own `package.json` and Node toolchain. **Alternative considered:** moving the backend into `/backend` for a symmetric monorepo — rejected for now because it churns every backend path (CI, alembic, docker-compose, codegraph) for a cosmetic gain, against the project's "complexity issue by issue" ethos. Promoting to symmetric later is a mechanical move when there is a reason.

### Tooling — pnpm + Vite + React + TypeScript + Tailwind
Vite provides the dev server (HMR) and the production bundler. pnpm is the package manager (the modern analog of `uv`). TypeScript is chosen for compiler-checked data shapes — higher correctness and a better learning signal than plain JS. **Alternatives:** Create React App / Webpack (superseded by Vite); npm/bun (pnpm preferred for speed and disk efficiency); plain JS (rejected — loses the typed-contract learning value).

### API access — plain `fetch` behind an `apiClient` wrapper
All calls go through one helper that prepends the base URL, attaches the bearer token, parses JSON, and throws on non-success. **Alternative considered:** TanStack Query from the start — deferred. Starting with `fetch` keeps the mechanism visible and avoids a second abstraction to learn; the wrapper is the seam where TanStack Query or a generated client slots in later without touching screens.

### Cross-origin — direct calls, no Vite proxy
The frontend calls the API directly at the `VITE_API_BASE_URL` origin (default `http://localhost:8077`). This assumes CORS is enabled on the backend, handled by a separate backend change landed before frontend implementation. **Alternative considered:** Vite dev proxy (same-origin, no CORS needed) — rejected per product decision to model the real deployed cross-origin setup rather than hide it behind a dev-only proxy.

### Types — hand-written for now
`Book` and auth payload types are written by hand. **Alternative considered:** generating types from `/openapi.json` — deferred to a future iteration once the manual baseline is understood. The `apiClient` seam keeps the later switch cheap.

### Token storage — keep it simple, isolated behind the client
The access token is held by the app and read by `apiClient` when composing requests. The exact storage mechanism is an implementation detail kept behind the client/auth state so it can be hardened later without touching call sites.

## Risks / Trade-offs

- **CORS dependency not yet in place** → The frontend cannot function until the backend enables CORS. Mitigation: a separate backend issue is tracked and implemented before frontend work begins; this change is authored assuming it is done.
- **Asymmetric layout may feel lopsided as the frontend grows** → Mitigation: layout is reversible; promote to `/backend` + `/frontend` only when friction is real.
- **Two toolchains (Python + Node) in one repo** → Mitigation: the Node toolchain is fully isolated under `/frontend`; backend commands and CI are untouched. Document both in `CLAUDE.md`.
- **Token handling is a security-sensitive area** → Mitigation: keep storage behind the client/auth seam so it can be revisited; out of scope to fully harden now.
- **Learning two technologies at once (React + TS)** → Mitigation: deliberately minimal scope (one login + one list) and no extra libraries until a concrete need appears.
