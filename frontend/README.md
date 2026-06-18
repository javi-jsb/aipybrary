# aipybrary frontend

A React + TypeScript + Tailwind single-page app (built with Vite, managed with
pnpm) for visualizing and exercising the aipybrary API. It logs in against the
backend, holds the returned JWT, and serves the protected views behind a routed,
authenticated layout. It now covers the full API surface: Books CRUD, Members
management, per-book copy management, and loans (borrow/return), with role-aware
controls (admin/staff/member) and client-side form validation.

## Stack

- React 19 + TypeScript
- React Router (`react-router`) for client-side routing
- TanStack Query (`@tanstack/react-query`) for server state
- Vite (dev server with HMR + production bundler)
- Tailwind CSS (via the `@tailwindcss/vite` plugin)
- ESLint + Prettier

## Setup

```bash
cd frontend
pnpm install
cp .env.example .env   # adjust VITE_API_BASE_URL if your backend isn't on :8077
pnpm dev
```

The dev server prints a local URL (default `http://localhost:5173`).

From the repo root you can also start it without `cd` via `make dev-frontend`
(runs `pnpm --dir frontend dev`); `pnpm install` still needs running once.

## Configuration

| Variable            | Description                                                                  |
| ------------------- | ---------------------------------------------------------------------------- |
| `VITE_API_BASE_URL` | Base URL of the backend API. Defaults to `http://localhost:8077` when unset. |

The frontend calls the API **directly cross-origin**, so the backend must have
CORS enabled for this origin (the dev origin is allowed by default; see the root
`CLAUDE.md` CORS section). There is no Vite dev proxy.

## Scripts

| Command             | Description                               |
| ------------------- | ----------------------------------------- |
| `pnpm dev`          | Start the dev server with HMR             |
| `pnpm build`        | Type-check and produce a production build |
| `pnpm preview`      | Preview the production build locally      |
| `pnpm typecheck`    | Type-check without emitting (`tsc -b`)    |
| `pnpm test`         | Run the Vitest suite once                 |
| `pnpm test:watch`   | Run Vitest in watch mode                  |
| `pnpm coverage`     | Run Vitest with a coverage report         |
| `pnpm lint`         | Run ESLint                                |
| `pnpm format`       | Format the codebase with Prettier         |
| `pnpm format:check` | Verify formatting without writing         |

## Layout

```
frontend/
  src/
    api/      apiClient wrapper, hand-written types, and per-resource typed call
              functions (books, members, bookCopies, loans, auth, users);
              errors.ts (ApiError → form-message helper)
    auth/     token storage seam, auth context/provider, useCurrentUser query,
              roles.ts (role → action gating helpers)
    components/  screens (LoginScreen, BooksList/BookForm, MembersList/
                 MemberDetail/MemberForm, BookCopies, LoansList/LoanForm),
                 status badges, *Validation.ts (client-side form rules),
                 ProtectedLayout (nav + sign-out)
    queryClient.ts  the single TanStack Query client
    routes.ts       shared route constants
    App.tsx   route tree (/login + protected resource routes)
    main.tsx  entry point (QueryClientProvider → BrowserRouter → AuthProvider)
```

Reads/writes go through TanStack Query over the `apiClient` seam, with mutations
invalidating the affected query keys so lists/details refresh. Routing is handled
by React Router behind `ProtectedLayout`, which redirects unauthenticated access
to `/login`. Role-aware controls (via `auth/roles.ts`) hide actions the current
user may not perform — this is UX-only, not a security boundary. Forms validate
client-side (the `*Validation.ts` modules) before submitting. See the root
`CLAUDE.md` frontend section for the full details.
