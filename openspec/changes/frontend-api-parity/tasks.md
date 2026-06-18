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

- [x] 2.1 Add typed call functions for `POST`, `PATCH`, `DELETE /books/{id}` on `apiClient`
- [x] 2.2 Book create form (route + `useMutation`), invalidating the books list on success
- [x] 2.3 Surface duplicate-ISBN (`409`) errors on the create/edit form
- [x] 2.4 Book edit form (`PATCH`), reflecting updated values after success
- [x] 2.5 Book delete action with confirmation; handle the "has copies" conflict
- [x] 2.6 Gate create/edit/delete controls by role
- [x] 2.7 Validate book fields client-side (required, lengths, ISBN checksum, integer year) to prevent avoidable `422`s

## 3. Members

- [x] 3.1 Add `Member` types and typed call functions (list, get, create, update)
- [x] 3.2 Members list view (`useQuery`) with navigation to detail
- [x] 3.3 Member detail view
- [x] 3.4 Member create form; display the one-time `initial_password` exactly once on success
- [x] 3.5 Member update form
- [x] 3.6 Gate member actions by role
- [x] 3.7 Member delete action (admin-only), inline in the list with confirmation; translate the backend `loans.member_id` FK RESTRICT into a `409 MemberHasLoansError` and surface it on the list

## 4. Book copies

- [x] 4.1 Add `BookCopy` types and typed call functions (list per book, add, remove)
- [x] 4.2 Copies view for a book (`useQuery`)
- [x] 4.3 Add-copy action, invalidating the copies and the book's availability
- [x] 4.4 Remove-copy action with appropriate error handling
- [x] 4.5 Gate copy actions by role

## 5. Loans

- [x] 5.1 Add `Loan` types and typed call functions (list, borrow, return)
- [x] 5.2 Loans list view (`useQuery`)
- [x] 5.3 Borrow form/action (select member + available copy), invalidating loans and availability
- [x] 5.4 Return action, reflecting the loan as returned
- [x] 5.5 Surface business-rule errors (no available copy, active-loan limit) on the form
- [x] 5.6 Gate loan actions by role

## 6. Documentation

- [ ] 6.1 Update root `CLAUDE.md` frontend section: routing, TanStack Query data layer, role-aware UI, new structure
- [ ] 6.2 Update `frontend/README.md`: routing/data-layer overview and any new scripts

## 7. Verification

- [ ] 7.1 With the backend running and seeded data, exercise each entity's actions end-to-end against the API
- [ ] 7.2 Confirm lists refresh after mutations (cache invalidation) and that error/role paths behave per the spec scenarios
- [ ] 7.3 `pnpm build`, `pnpm lint`, `pnpm format:check` all green
