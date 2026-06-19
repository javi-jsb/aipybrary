import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.sorting import SortOrder
from app.database import get_session
from app.members.application.member_service import MemberService
from app.members.domain.member_exceptions import DuplicateEmailError, MemberHasLoansError
from app.members.domain.member_model import (
    MemberCreate,
    MemberCreateResponse,
    MemberListResponse,
    MemberPublic,
    MemberStatus,
    MemberUpdate,
    SortBy,
)
from app.members.infrastructure.sql_member_repository import SqlModelMemberRepository
from app.users.infrastructure.authz import require_self_or_staff, staff_only
from app.users.infrastructure.sql_user_repository import SqlModelUserRepository

router = APIRouter(prefix="/members", tags=["members"])

_DUPLICATE_EMAIL_DETAIL = "Email already registered"
_HAS_LOANS_DETAIL = "Member has loans and cannot be deleted"

# Listing and managing members is admin/staff only; reading a single member is
# allowed to admin/staff or to the member themselves (ownership-scoped).
_STAFF_ONLY = [Depends(staff_only)]
_SELF_OR_STAFF = [Depends(require_self_or_staff)]


def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> MemberService:
    return MemberService(
        user_repository=SqlModelUserRepository(session),
        member_repository=SqlModelMemberRepository(session),
    )


ServiceDep = Annotated[MemberService, Depends(_get_service)]


@router.get("", response_model=MemberListResponse, dependencies=_STAFF_ONLY)
async def list_members(
    service: ServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    full_name: str | None = None,
    email: str | None = None,
    status: MemberStatus | None = None,
    sort_by: SortBy = SortBy.created_at,
    order: SortOrder = SortOrder.desc,
) -> MemberListResponse:
    return await service.get_filtered(full_name, email, status, sort_by, order, page, size)


@router.get("/{member_id}", response_model=MemberPublic, dependencies=_SELF_OR_STAFF)
async def get_member(member_id: uuid.UUID, service: ServiceDep) -> MemberPublic:
    result = await service.get_by_id(member_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    member, email = result
    return MemberPublic.from_member(member, email)


@router.post("", response_model=MemberCreateResponse, status_code=status.HTTP_201_CREATED, dependencies=_STAFF_ONLY)
async def create_member(data: MemberCreate, service: ServiceDep) -> MemberCreateResponse:
    try:
        return await service.create(data)
    except DuplicateEmailError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_EMAIL_DETAIL) from None


@router.patch("/{member_id}", response_model=MemberPublic, dependencies=_STAFF_ONLY)
async def update_member(member_id: uuid.UUID, data: MemberUpdate, service: ServiceDep) -> MemberPublic:
    result = await service.update(member_id, data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    member, email = result
    return MemberPublic.from_member(member, email)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_STAFF_ONLY)
async def delete_member(member_id: uuid.UUID, service: ServiceDep) -> None:
    try:
        deleted = await service.delete(member_id)
    except MemberHasLoansError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_HAS_LOANS_DETAIL) from None
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
