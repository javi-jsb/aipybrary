import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.members.application.member_service import MemberService
from app.members.domain.member_exceptions import DuplicateEmailError
from app.members.domain.member_model import (
    MemberCreate,
    MemberListResponse,
    MemberPublic,
    MemberStatus,
    MemberUpdate,
    SortBy,
    SortOrder,
)
from app.members.infrastructure.sql_member_repository import SqlModelMemberRepository

router = APIRouter(prefix="/members", tags=["members"])

_DUPLICATE_EMAIL_DETAIL = "Email already registered"


def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> MemberService:
    return MemberService(SqlModelMemberRepository(session))


ServiceDep = Annotated[MemberService, Depends(_get_service)]


@router.get("", response_model=MemberListResponse)
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


@router.get("/{member_id}", response_model=MemberPublic)
async def get_member(member_id: uuid.UUID, service: ServiceDep) -> MemberPublic:
    member = await service.get_by_id(member_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return MemberPublic.model_validate(member)


@router.post("", response_model=MemberPublic, status_code=status.HTTP_201_CREATED)
async def create_member(data: MemberCreate, service: ServiceDep) -> MemberPublic:
    try:
        member = await service.create(data)
    except DuplicateEmailError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_EMAIL_DETAIL) from None
    return MemberPublic.model_validate(member)


@router.patch("/{member_id}", response_model=MemberPublic)
async def update_member(member_id: uuid.UUID, data: MemberUpdate, service: ServiceDep) -> MemberPublic:
    try:
        member = await service.update(member_id, data)
    except DuplicateEmailError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_EMAIL_DETAIL) from None
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return MemberPublic.model_validate(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: uuid.UUID, service: ServiceDep) -> None:
    deleted = await service.delete(member_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
