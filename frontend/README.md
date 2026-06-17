# aipybrary frontend

A React + TypeScript + Tailwind single-page app (built with Vite, managed with
pnpm) for visualizing and exercising the aipybrary API. It logs in against the
backend, holds the returned JWT, and serves the protected views behind a routed,
authenticated layout. Entity views are added incrementally (Books list first).

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
| `pnpm lint`         | Run ESLint                                |
| `pnpm format`       | Format the codebase with Prettier         |
| `pnpm format:check` | Verify formatting without writing         |

## Layout

```
frontend/
  src/
    api/      apiClient wrapper, hand-written types, typed call functions,
              errors.ts (ApiError → form-message helper)
    auth/     token storage seam, auth context/provider, useCurrentUser query
    components/  LoginScreen, BooksList, ProtectedLayout (nav + sign-out)
    queryClient.ts  the single TanStack Query client
    routes.ts       shared route constants
    App.tsx   route tree (/login + protected routes)
    main.tsx  entry point (QueryClientProvider → BrowserRouter → AuthProvider)
```

Reads/writes go through TanStack Query over the `apiClient` seam; routing is
handled by React Router behind `ProtectedLayout`, which redirects unauthenticated
access to `/login`. See the root `CLAUDE.md` frontend section for details.
