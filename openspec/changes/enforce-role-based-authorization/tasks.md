## 1. Backend — authorization primitive (issue #89)

- [x] 1.1 Add `require_role(*roles: UserRole)` dependency factory layered on `get_current_user`, raising `403` (distinct from `401`) when the caller's role is not allowed (location per design: `app/users/infrastructure/authz.py`)
- [x] 1.2 Add `MemberRepository.get_by_user_id(user_id)` to the ABC and its `SqlModelMemberRepository` implementation (`SELECT ... WHERE members.user_id = :user_id`)
- [x] 1.3 Add a member-ownership dependency (e.g. `require_self_or_staff`) that allows `admin`/`staff` unconditionally and a `member` only for their own resolved member; deny with `403` when there is no linked member
- [ ] 1.4 Unit-test the primitives in isolation: role allow/deny, `401` vs `403`, ownership allow/deny, missing-linked-member case

## 2. Backend — apply the matrix to routers (issue #89)

- [x] 2.1 Books router: guard POST/PATCH/DELETE with `require_role(admin, staff)`; leave GETs on the plain auth gate
- [x] 2.2 Book-copies router: same write-vs-read split as books
- [x] 2.3 Members router: guard list/create/update/delete for `admin`/`staff`; guard `GET /members/{id}` with the ownership rule (member reads only their own); reject member listing with `403`
- [x] 2.4 Loans router: guard borrow/return/undo-return/cancel for `admin`/`staff`; scope `GET /loans` to the caller's own member when the caller is a `member` (override any `member_id` filter); reject a member reading another member's `GET /loans/{id}` with `403`
- [x] 2.5 Reconcile `main.py` `_auth_gate` wiring with the per-route guards so authentication still applies everywhere and `/auth/me` stays available to all authenticated users

## 3. Backend — test the authorization matrix (issue #89)

- [x] 3.1 Extend `tests/conftest.py`: add `admin` and `member` caller fixtures/overrides alongside the existing fake-`staff` `client`
- [x] 3.2 Table-driven per-endpoint matrix tests (each role × each route): allow/deny and the correct status (`403` vs `401`)
- [x] 3.3 Ownership/scoping tests: member reads own profile/loans (allowed), member reads another's profile/loan (`403`), member loan list scoped to self, member cannot borrow/return/cancel
- [x] 3.4 Confirm coverage stays near the project target; mark only genuinely untestable lines with `# pragma: no cover`

## 4. Backend — docs (issue #89)

- [x] 4.1 Update `CLAUDE.md` auth-gate section: the backend now enforces role authorization (remove the "not enforced" note); document `require_role`/ownership and the `403` vs `401` distinction

## 5. Frontend — mirror the matrix (issue #90, after backend)

- [ ] 5.1 Extend `src/auth/roles.ts` with the new rules: a `member` sees only their own loans and has no members/users list or nav
- [ ] 5.2 Scope the loans view for a `member` to their own loans (query keyed by their member id) and hide borrow/return controls
- [ ] 5.3 Hide the members/users navigation and routes for roles without access
- [ ] 5.4 Add a shared `403` handling path (friendly "not allowed" message / redirect) distinct from the `401`/session-expired path, using the `ApiError` status from `apiClient`

## 6. Frontend — tests and docs (issue #90)

- [ ] 6.1 Tests: `roles.ts` gating helpers per role, member loans-view scoping, members nav/route hiding, and the `403` handling path
- [ ] 6.2 Update `CLAUDE.md` "Role-aware UI" section to reflect that the backend now enforces the matrix and the frontend mirrors it (no longer "UX-only / not enforced anywhere")
- [ ] 6.3 Update the Help screen (`src/components/HelpScreen.tsx`) capability matrix / prose for the new member self-scoping and hidden members list

## 7. End-to-end coverage (optional, aligns with existing e2e suite)

- [ ] 7.1 Extend the role-aware visibility e2e spec to assert a `member` is denied (or sees scoped data) on members and loan-management flows against the real stack
