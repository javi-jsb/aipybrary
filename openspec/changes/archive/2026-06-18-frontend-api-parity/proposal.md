## Why

`frontend-foundation` shipped a single read-only slice (login + Books list) and deferred everything else. To actually use the SPA as an API client — the whole point of building it — it must let the user perform **every action the API exposes** (create/edit/delete books, manage members, copies, and loans), not just read books.

## What Changes

- Introduce **client-side routing** so the app has multiple navigable views instead of a single gated screen, with a shared authenticated layout (navigation + sign-out).
- Adopt **TanStack Query** as the data layer, layered on the existing `apiClient` seam, so server state (caching, loading/error, invalidation after mutations) is handled consistently instead of hand-rolled `useEffect` fetches.
- **Books**: add create, edit, and delete on top of the existing list/detail.
- **Members**: list, detail, create (surfacing the one-time `initial_password` from `MemberCreateResponse`), and update.
- **Book copies**: list per book, add a copy, remove a copy.
- **Loans**: list, borrow (create), and return.
- **Role-aware UI**: surface/hide actions based on the authenticated user's role (`admin` / `staff` / `member`), resolved via `GET /auth/me`.
- **Consistent forms**: shared validation and error handling driven by the `apiClient`/`ApiError` seam (e.g. surface `409`/`422` detail messages on the relevant form).
- Keep **hand-written TypeScript types**, extended per entity (`Member`, `BookCopy`, `Loan`, and their create/update payloads), consistent with the existing `src/api/types.ts`.

Out of scope: generating types from `/openapi.json` (deferred — kept hand-written for now; the `apiClient` seam keeps a later switch cheap), production deployment/build-serve integration, CORS hardening, a dedicated frontend CI job, real-time updates, and any new backend endpoints (this change consumes the existing API only).

## Capabilities

### New Capabilities
<!-- None. This expands the existing web-frontend capability. -->

### Modified Capabilities
- `web-frontend`: Add requirements for client-side routing and an authenticated layout, role-aware action gating, full Books CRUD, Member management (incl. one-time initial password display), Book-copy management, and Loan borrow/return — all routed through the shared API client with consistent form validation and error surfacing.

## Impact

- **Frontend code** (`/frontend`): new routing, an authenticated layout shell, per-entity views/forms, a TanStack Query setup, and a generated-types pipeline. The `apiClient`/`tokenStore` seam is reused, not replaced.
- **New frontend dependencies**: a router (React Router) and TanStack Query — both isolated under `/frontend`. Types stay hand-written (no codegen dependency).
- **Backend**: untouched — consumes existing `books`, `members`, `book_copies`, `loans`, and `auth` endpoints only.
- **Docs**: root `CLAUDE.md` frontend section and `frontend/README.md` updated (routing, data layer, type generation, new scripts).
- **Process**: implemented as per-entity slices (umbrella issue #64), each its own issue + PR.
