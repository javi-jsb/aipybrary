## Why

Authentication proves *who* you are, but the app enforces nothing about *what* you may do: every route sits behind a single auth gate (`_auth_gate = [Depends(get_current_user)]`) and any valid JWT — including a `member`'s — can list every user/member, read anyone's loans, and create/edit/delete books, copies, and loans. Role gating today is **UX-only** (the frontend's `roles.ts` hides controls), which is trivially bypassed by calling the API directly. This change makes authorization a real, server-enforced security boundary, with the frontend mirroring it for UX.

## What Changes

- **Backend (the security boundary — issue #89):**
  - Add a reusable FastAPI authorization layer on top of `get_current_user`: a `require_role(*roles)` dependency and an ownership variant for member self-access.
  - Apply the permission matrix to every router (books, book-copies, members, loans, and `GET /auth/me`):
    - Manage books / copies → `admin`, `staff`. Members read-only.
    - List / manage members → `admin`, `staff`. A `member` may read **only their own** profile.
    - Borrow / return / cancel loans → `admin`, `staff` (no member self-service this iteration).
    - List loans → `admin`/`staff` see all; a `member` is scoped to `member_id == self`; reading another member's loans → `403`.
  - Resolve a `member`-role caller to their `Member` row (new `MemberRepository.get_by_user_id`) so ownership rules can be evaluated.
  - Return **`403 Forbidden`** for authenticated-but-unauthorized, distinct from `401`.
- **Frontend (UX mirror — issue #90, depends on the backend):**
  - Extend `roles.ts` to the new rules: a `member` sees only their own loans and no members/users list/nav.
  - Scope the loans view for a `member` to their own loans; hide members nav/routes for roles without access.
  - Handle `403` responses gracefully (friendly message / redirect), not just by hiding controls.
- **Docs:** update `CLAUDE.md` — the auth-gate and "Role-aware UI" sections currently state the backend does **not** enforce role authorization; that must flip.

## Capabilities

### New Capabilities
- `authorization`: Server-side role-based access control — the permission matrix per endpoint (admin/staff/member), the `require_role` / member-ownership dependencies, member self-scoping for profile and loan reads, and the `403` vs `401` distinction. This is the security boundary; the frontend is not trusted.

### Modified Capabilities
- `web-frontend`: The existing "Role-aware action visibility" requirement is extended from UX-only hiding to mirroring an enforced backend matrix — member loan self-scoping, hidden members/users nav, and graceful `403` handling.

## Impact

- **Backend code:** new authorization dependency module (likely `app/users/infrastructure/authz.py` or `app/core/`), wiring changes in `main.py` (`_auth_gate` composition) and every router; new `MemberRepository.get_by_user_id` + SQL implementation; loan-listing scope enforcement.
- **Tests:** per-endpoint authorization matrix (each role × each route) incl. ownership/scoping cases. `tests/conftest.py` currently overrides `get_current_user` with a fake **staff** user — add `admin` and `member` caller fixtures/parametrization.
- **Frontend code:** `roles.ts`, loans view scoping, members nav/route gating, a shared `403` handling path, and their tests.
- **API behavior change:** previously-permitted calls for a `member` now return `403` — a deliberate, security-positive break for any client relying on the old permissive behavior. No DB schema/migration change.
- **Docs:** `CLAUDE.md` auth-gate + "Role-aware UI" sections.
