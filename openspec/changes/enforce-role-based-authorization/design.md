## Context

Every protected route is mounted behind one dependency in `main.py`:

```python
_auth_gate = [Depends(get_current_user)]
app.include_router(books_router, dependencies=_auth_gate)
# ... book_copies, members, loans
```

`get_current_user` (`app/users/infrastructure/auth_router.py`) decodes the JWT, loads the `User`, and checks `is_active` — it proves *identity* and nothing else. `User.role` (`admin`/`staff`/`member`) is carried but never consulted for access decisions. The result: a `member`'s token can call any endpoint. The frontend's `roles.ts` only *hides* controls and is explicitly documented as not a security boundary.

This is a cross-cutting change: a new backend authorization layer applied to four routers plus `/auth/me`, ownership resolution that crosses the users↔members slice boundary, and a frontend mirror. It warrants a design doc for the dependency shape, the ownership lookup, and the loan-scoping decision.

## Goals / Non-Goals

**Goals:**
- A single, reusable, tested authorization primitive (`require_role`) usable as both a router-level and route-level dependency.
- Enforce the permission matrix server-side on every endpoint, returning `403` (not `401`) for authenticated-but-unauthorized callers.
- Member self-access: a `member` may read their own profile and their own loans, and nothing else members-related.
- Frontend mirrors the matrix for UX and degrades gracefully on `403`.

**Non-Goals:**
- Member self-service borrow/return (members stay read-only on loans this iteration).
- Per-object ACLs, permission tables, or a policy engine — the matrix is small and static; hard-coded role sets are sufficient.
- Changing the JWT contract, token lifetime, or the login flow.
- Reworking `roles.ts` into a shared codegen'd source with the backend — the two matrices are maintained in parallel and kept in sync by tests/docs.

## Decisions

### 1. `require_role(*roles)` as a FastAPI dependency factory

A factory returning a dependency that re-uses `get_current_user`, compares `current_user.role` against the allowed set, and raises `403` otherwise:

```python
def require_role(*roles: UserRole):
    async def _dep(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return _current_user
    return _dep
```

- **Router-level for the simple cases:** books and book-copies are a clean split — reads open to any authenticated user, writes `admin`/`staff`. Rather than one router-wide gate, apply `Depends(require_role(...))` per write route (POST/PATCH/DELETE) and leave GETs on the plain auth gate. Keeps the matrix visible at each route.
- **Why not middleware / a global matrix table:** path→role mapping in middleware drifts from the routes and is invisible at the handler. Per-route dependencies live next to the handler, are type-checked, and FastAPI renders them in `/docs`.
- **Alternative considered — encode role checks in services:** rejected; authorization is an HTTP-boundary concern and belongs in the router layer, keeping services free of request identity.

### 2. Member ownership resolution — new `MemberRepository.get_by_user_id`

Ownership rules ("a member reads their own profile / own loans") need to map a `member`-role `User` to their `Member` row. There is no such lookup today (`MemberRepository` keys only by `member_id`). Add:

```python
async def get_by_user_id(self, user_id: uuid.UUID) -> Member | None
```

backed by a `SELECT ... WHERE members.user_id = :user_id`. The ownership dependency (e.g. `require_self_or_staff`) uses it to compare the path's `member_id` against the caller's own `Member.id`:
- `admin`/`staff` → allowed unconditionally.
- `member` → allowed only when the target `member_id` resolves to their own row; otherwise `403`.

### 3. Loan listing is *scoped*, not just gated

`GET /loans` for a `member` must return only their own loans, not `403`. Decision: when the caller is a `member`, the router forces `member_id = <caller's own member id>` (overriding any query param) before calling the service; `admin`/`staff` keep the existing free filtering. A member requesting `GET /loans/{id}` for a loan that isn't theirs → `403` (or `404` to avoid leaking existence — see Open Questions). Borrow/return/cancel stay `admin`/`staff` only via `require_role`.

### 4. `403` vs `401` discipline

`get_current_user` already raises `401` for missing/invalid tokens. The new layer raises `403` for valid-token-but-wrong-role. This is the standard distinction and lets the frontend tell "log in again" from "you can't do this."

### 5. Frontend mirror

`roles.ts` stays the single UX gating source. Extend it with the member-loan and members-nav rules, scope the loans view query for members, hide the members nav/routes, and add a shared `403` handler (the `apiClient` already throws `ApiError` with a status — surface a friendly "not allowed" message / redirect rather than a raw error). Frontend remains UX-only and untrusted.

## Risks / Trade-offs

- **Test surface explosion (role × route).** → Parametrize over roles in `conftest.py` (add `admin`/`member` caller fixtures alongside the existing fake-staff) and table-drive the matrix so each route asserts allow/deny per role with minimal boilerplate.
- **Behavior break for any member-token client.** → Intended and security-positive; called out in the proposal. No external consumers today beyond the SPA, which is updated in the same epic.
- **Two matrices (backend + `roles.ts`) can drift.** → The backend is authoritative; `roles.ts` is cosmetic. Keep them aligned via the Help-screen capability matrix and tests; a future iteration may codegen from one source.
- **Ownership lookup adds a query per member request.** → One indexed lookup by `user_id`; negligible, and only on the member path.

## Migration Plan

No DB migration. Roll out backend (#89) first so the boundary exists, then the frontend mirror (#90) so the UI matches what the API allows. Rollback is reverting the router dependencies; the `get_by_user_id` addition is inert on its own.

## Open Questions

- **`403` vs `404` for a member reading another member's resource** (profile or loan). `403` is honest; `404` avoids leaking existence. Lean `403` for consistency with the rest of the matrix unless existence-leak is judged a concern — confirm during implementation.
- **Where the dependency module lives:** `app/users/infrastructure/authz.py` (next to `get_current_user`) vs `app/core/`. Leaning `users/infrastructure` since it depends on `User`/`UserRole` and `get_current_user`; `app/core` is a leaf and must not import slices.
