"""Role-based authorization layered on top of `get_current_user`.

`get_current_user` proves *identity* (a valid, active user); this module proves
*permission* (the right role / ownership for the route). Authentication failures
surface as `401` from `get_current_user`; authorization failures surface here as
`403`, so the two are always distinguishable.

This is the security boundary — the frontend's `roles.ts` only hides controls and
must not be trusted. Cross-slice infrastructure import of the member repository is
deliberate: ownership rules ("a member may act only on their own record") need to
resolve a `member`-role user to their `Member`.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.members.domain.member_model import Member
from app.members.infrastructure.sql_member_repository import SqlModelMemberRepository
from app.users.domain.user_model import User, UserRole
from app.users.infrastructure.auth_router import get_current_user

CurrentUserDep = Annotated[User, Depends(get_current_user)]

#: Roles with full staff-facing access (manage catalog, members, and loans).
STAFF_ROLES = (UserRole.admin, UserRole.staff)

FORBIDDEN = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def require_role(*roles: UserRole):
    """Dependency factory: admit the request only when the caller's role is allowed.

    Layered on `get_current_user`, so a missing/invalid token still yields `401`
    from that dependency before this check runs; a valid token with the wrong role
    yields `403`.
    """

    async def _dependency(current_user: CurrentUserDep) -> User:
        if current_user.role not in roles:
            raise FORBIDDEN
        return current_user

    return _dependency


#: Shared dependency for the common admin/staff-only routes (catalog/member/loan writes).
staff_only = require_role(*STAFF_ROLES)


def _get_member_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> SqlModelMemberRepository:
    return SqlModelMemberRepository(session)


MemberRepoDep = Annotated[SqlModelMemberRepository, Depends(_get_member_repo)]


async def resolve_own_member(current_user: User, repo: SqlModelMemberRepository) -> Member:
    """Resolve a caller's linked member record, or raise `403` when there is none.

    A `member`-role user with no linked `Member` cannot own anything, so
    ownership-scoped access is denied rather than erroring.
    """
    member = await repo.get_by_user_id(current_user.id)
    if member is None:
        raise FORBIDDEN
    return member


async def require_self_or_staff(
    member_id: uuid.UUID,
    current_user: CurrentUserDep,
    repo: MemberRepoDep,
) -> User:
    """Allow `admin`/`staff` unconditionally; allow a `member` only for their own id."""
    if current_user.role in STAFF_ROLES:
        return current_user
    member = await resolve_own_member(current_user, repo)
    if member.id != member_id:
        raise FORBIDDEN
    return current_user
