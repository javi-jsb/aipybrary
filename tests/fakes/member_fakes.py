import uuid

from app.members.domain.member_model import (
    Member,
    MemberCreate,
    MemberStatus,
    MemberUpdate,
    SortBy,
    SortOrder,
)
from app.members.domain.member_repository import MemberRepository


class FakeMemberRepository(MemberRepository):
    def __init__(self) -> None:
        self._members: dict[uuid.UUID, Member] = {}

    def add(self, member: Member) -> None:
        self._members[member.id] = member

    async def create(self, data: MemberCreate) -> Member:
        member = Member.model_validate(data)
        self._members[member.id] = member
        return member

    async def get_by_id(self, member_id: uuid.UUID) -> Member | None:
        return self._members.get(member_id)

    async def get_filtered(
        self,
        full_name: str | None,
        email: str | None,
        status: MemberStatus | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[Member], int]:
        members = list(self._members.values())
        if full_name:
            members = [m for m in members if full_name.lower() in m.full_name.lower()]
        if email:
            members = [m for m in members if email.lower() in m.email.lower()]
        if status is not None:
            members = [m for m in members if m.status == status]
        total = len(members)
        offset = (page - 1) * size
        return members[offset : offset + size], total

    async def update(self, member: Member, data: MemberUpdate) -> Member:
        member.sqlmodel_update(data.model_dump(exclude_unset=True))
        return member

    async def delete(self, member: Member) -> None:
        self._members.pop(member.id, None)
