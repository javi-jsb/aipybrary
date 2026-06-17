## 1. Foundation (routing, data layer, layout)

- [x] 1.1 Add dependencies: `react-router` and `@tanstack/react-query` (isolated under `/frontend`)
- [x] 1.2 Wrap the app in a `QueryClientProvider` (single `QueryClient`) alongside the existing `AuthProvider`
- [x] 1.3 Introduce React Router: replace the `App.tsx` boolean toggle with a route tree (login route + protected routes)
- [x] 1.4 Build the authenticated layout: nav + sign-out + `<Outlet/>`; redirect unauthenticated access to `/login`
- [x] 1.5 Move `LoginScreen` to a route and navigate to the default authenticated route on success
- [x] 1.6 Add a `useCurrentUser` query (`GET /auth/me`) and expose the role for role-aware UI gating
- [x] 1.7 Add a shared helper that maps a thrown `ApiError` to form-level messages (surfacing `409`/`422` detail)
- [x] 1.8 Port the existing Books list to `useQuery` + the new layout/route (no behavior change)

## 2. Books CRUD

- [ ] 2.1 Add typed call functions for `POST`, `PATCH`, `DELETE /books/{id}` on `apiClient`
- [ ] 2.2 Book create form (route + `useMutation`), invalidating the books list on success
- [ ] 2.3 Surface duplicate-ISBN (`409`) errors on the create/edit form
- [ ] 2.4 Book edit form (`PATCH`), reflecting updated values after success
- [ ] 2.5 Book delete action with confirmation; handle the "has copies" conflict
- [ ] 2.6 Gate create/edit/delete controls by role

## 3. Members

- [ ] 3.1 Add `Member` types and typed call functions (list, get, create, update)
- [ ] 3.2 Members list view (`useQuery`) with navigation to detail
- [ ] 3.3 Member detail view
- [ ] 3.4 Member create form; display the one-time `initial_password` exactly once on success
- [ ] 3.5 Member update form
- [ ] 3.6 Gate member actions by role

## 4. Book copies

- [ ] 4.1 Add `BookCopy` types and typed call functions (list per book, add, remove)
- [ ] 4.2 Copies view for a book (`useQuery`)
- [ ] 4.3 Add-copy action, invalidating the copies and the book's availability
- [ ] 4.4 Remove-copy action with appropriate error handling
- [ ] 4.5 Gate copy actions by role

## 5. Loans

- [ ] 5.1 Add `Loan` types and typed call functions (list, borrow, return)
- [ ] 5.2 Loans list view (`useQuery`)
- [ ] 5.3 Borrow form/action (select member + available copy), invalidating loans and availability
- [ ] 5.4 Return action, reflecting the loan as returned
- [ ] 5.5 Surface business-rule errors (no available copy, active-loan limit) on the form
- [ ] 5.6 Gate loan actions by role

## 6. Documentation

- [ ] 6.1 Update root `CLAUDE.md` frontend section: routing, TanStack Query data layer, role-aware UI, new structure
- [ ] 6.2 Update `frontend/README.md`: routing/data-layer overview and any new scripts

## 7. Verification

- [ ] 7.1 With the backend running and seeded data, exercise each entity's actions end-to-end against the API
- [ ] 7.2 Confirm lists refresh after mutations (cache invalidation) and that error/role paths behave per the spec scenarios
- [ ] 7.3 `pnpm build`, `pnpm lint`, `pnpm format:check` all green
