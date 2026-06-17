## Context

`frontend-foundation` delivered the SPA skeleton: a Vite + React + TS + Tailwind app, a shared `apiClient` (base URL + bearer token + JSON + `ApiError`), a `tokenStore` seam, an `AuthContext`/`AuthProvider`, and a single gated screen (`App.tsx` toggles `LoginScreen` vs `BooksList`). Server state is fetched ad hoc with `useEffect` + an `active` guard.

That structure does not scale to the full API surface (Books CRUD, Members, Book copies, Loans), which needs multiple navigable views, detail pages with ids, and mutations that must keep lists fresh. This change settles the architectural decisions deferred in `frontend-foundation` and lays the patterns that the per-entity slices will follow. It is purely additive on the frontend and consumes only existing backend endpoints.

## Goals / Non-Goals

**Goals:**
- Multi-view navigation with real URLs, browser history, and deep-linking behind an authenticated layout.
- A single, consistent server-state pattern (cache, loading/error, invalidation after mutations) built on the existing `apiClient` seam.
- Full parity with the API's actions for Books, Members, Book copies, and Loans, with consistent form validation/error surfacing.
- Establish patterns once; implement entities incrementally as separate slices/PRs.

**Non-Goals:**
- Generating types from `/openapi.json` (kept hand-written; deferred).
- Backend changes of any kind, including endpoint-level role authorization.
- Production build/serve, CORS hardening, a frontend CI job, real-time updates.
- A component/design system or form library (kept lean — see Decisions).

## Decisions

### Routing — React Router
Adopt React Router for client-side routing: an authenticated layout route (nav + sign-out + `<Outlet/>`) wrapping resource routes (`/books`, `/books/:id`, `/books/new`, `/members`, `/loans`, …), with unauthenticated access redirected to `/login`. **Alternatives:** hand-rolled `useState` view switching (rejected — loses URLs, back/forward, deep-linking, F5 persistence; does not scale to ~10 views) and `wouter` (lighter, but React Router is the standard with higher learning value). Routing for a multi-view SPA is effectively unavoidable; the only real question was which library.

### Data layer — TanStack Query over `apiClient`
Use TanStack Query for all server state, with query functions delegating to the existing `apiClient`. Reads use `useQuery` with per-resource query keys (e.g. `["books", filters]`, `["book", id]`); writes use `useMutation` that calls `apiClient` and invalidates the affected keys so lists/details refresh automatically. **Alternative considered:** continue with `useEffect` + manual state (rejected — every list/detail would re-implement loading/error/race handling, and every mutation would manually re-fetch; this is exactly the `active`-flag boilerplate from `BooksList`). `apiClient`/`tokenStore` are reused unchanged — TanStack Query layers on top of the seam, it does not replace it.

### Types — hand-written
Extend the existing hand-written types in `src/api/types.ts` per entity rather than generating from OpenAPI. **Rationale:** with one repo, deliberate API changes, and ~4 entities, drift risk is low, and codegen adds a dependency, a build step, and the discipline of regenerating (whose absence silently re-introduces drift). The `apiClient`/types seam keeps a later switch to generated types cheap. Documented as a future improvement.

### Authenticated layout & route gating
A protected layout component checks `isAuthenticated` (from `AuthContext`) and renders the nav shell + `<Outlet/>`, or redirects to `/login`. `LoginScreen` becomes a route; on success it navigates to the default authenticated route. This replaces the boolean toggle in `App.tsx`.

### Role-aware UI is UX-only
Resolve the current user via `GET /auth/me` (cached with TanStack Query) and expose the role on the auth context so the UI can show/hide actions per role (`admin`/`staff`/`member`). **Important:** the backend auth gate currently enforces *authentication* only, not endpoint-level *authorization* by role, so this gating is cosmetic/UX — not a security boundary. Real authorization, if needed, is a separate backend change.

### Forms & error handling — lean, on the existing seam
Controlled inputs (same style as `LoginScreen`), no form library. A small shared helper maps a thrown `ApiError` to form-level messages, surfacing backend `detail` for `409` (e.g. duplicate ISBN) and `422` (validation). **Alternative:** a form library (react-hook-form) — deferred to keep dependencies minimal; revisit only if forms grow complex.

Forms also validate **client-side before submitting**, mirroring the backend's field constraints (required, max lengths, ISBN-10/13 checksum, integer year) so predictable `422`s never cost a round-trip; invalid input shows per-field messages and the request is not sent. Conflicts that are not knowable on the client (a duplicate ISBN, `409`) still come from the server. **Trade-off:** the client rules duplicate the backend's and can drift — kept lean, co-located with each form in a testable module, and called out in `CLAUDE.md` to keep in sync. `409`/`422` handling via the shared helper remains the backstop for anything the client misses.

### Incremental delivery
Patterns (router, query client, layout) land first; then one entity per slice/PR — Books CRUD → Members → Book copies → Loans — each its own issue under umbrella #64.

## Risks / Trade-offs

- **Two new libraries at once (React Router + TanStack Query)** → Mitigation: introduce both in the foundational slice with the simplest idioms; entity slices then just follow the pattern.
- **Role-aware UI mistaken for security** → Mitigation: document explicitly that it is UX-only; the server is the authority. Hiding a button is not access control.
- **Mutations leaving stale caches** → Mitigation: standardize query keys and always `invalidateQueries` for the affected resource in each mutation.
- **Pagination/filtering UX** (the list endpoints are paginated) → Mitigation: start with minimal controls (page next/prev, existing title/author filters for books); richer UX is incremental.
- **Scope across four entities** → Mitigation: per-entity slices keep each PR reviewable and shippable.

## Open Questions

- Exact role→action matrix for the UX gating (which actions each of `admin`/`staff`/`member` sees) — to be pinned per entity slice, given the backend does not currently enforce it.
- Depth of pagination/filter UI in the first pass vs. later polish.
