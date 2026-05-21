import uuid

from app.core.sorting import SortOrder
from app.members.domain.member_model import (
    Member,
    MemberCreate,
    MemberListResponse,
    MemberPublic,
    MemberStatus,
    MemberUpdate,
    SortBy,
)
from app.members.domain.member_repository import MemberRepository


class MemberService:
    def __init__(self, repository: MemberRepository) -> None:
        self._repository = repository

    async def create(self, data: MemberCreate) -> Member:
        return await self._repository.create(data)

    async def get_by_id(self, member_id: uuid.UUID) -> Member | None:
        return await self._repository.get_by_id(member_id)

    async def get_filtered(
        self,
        full_name: str | None,
        email: str | None,
        status: MemberStatus | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> MemberListResponse:
        members, total = await self._repository.get_filtered(full_name, email, status, sort_by, order, page, size)
        items = [MemberPublic.model_validate(m) for m in members]
        return MemberListResponse(items=items, total=total, page=page, size=size)

    async def update(self, member_id: uuid.UUID, data: MemberUpdate) -> Member | None:
        member = await self._repository.get_by_id(member_id)
        if member is None:
            return None
        return await self._repository.update(member, data)

    async def delete(self, member_id: uuid.UUID) -> bool:
        member = await self._repository.get_by_id(member_id)
        if member is None:
            return False
        await self._repository.delete(member)
        return True
