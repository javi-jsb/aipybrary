import uuid

from app.core.sorting import SortOrder
from app.members.domain.member_model import (
    Member,
    MemberStatus,
    MemberUpdate,
    SortBy,
)
from app.members.domain.member_repository import MemberRepository
from tests.fakes.user_fakes import FakeUserRepository


class FakeMemberRepository(MemberRepository):
    def __init__(self, user_repo: FakeUserRepository | None = None) -> None:
        self._user_repo = user_repo
        self._members: dict[uuid.UUID, Member] = {}

    def add(self, member: Member) -> None:
        self._members[member.id] = member

    def _email(self, member: Member) -> str:
        if self._user_repo is None:
            return ""
        user = self._user_repo._users.get(member.user_id)
        return user.email if user else ""

    async def create(self, member: Member) -> Member:
        self._members[member.id] = member
        return member

    async def get_by_id(self, member_id: uuid.UUID) -> Member | None:
        return self._members.get(member_id)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Member | None:
        return next((m for m in self._members.values() if m.user_id == user_id), None)

    async def get_by_id_with_email(self, member_id: uuid.UUID) -> tuple[Member, str] | None:
        member = self._members.get(member_id)
        if member is None:
            return None
        return member, self._email(member)

    async def get_filtered(
        self,
        full_name: str | None,
        email: str | None,
        status: MemberStatus | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[tuple[Member, str]], int]:
        pairs = [(m, self._email(m)) for m in self._members.values()]
        if full_name:
            pairs = [(m, e) for m, e in pairs if full_name.lower() in m.full_name.lower()]
        if email:
            pairs = [(m, e) for m, e in pairs if email.lower() in e.lower()]
        if status is not None:
            pairs = [(m, e) for m, e in pairs if m.status == status]
        total = len(pairs)
        offset = (page - 1) * size
        return pairs[offset : offset + size], total

    async def update(self, member: Member, data: MemberUpdate) -> Member:
        member.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._members[member.id] = member
        return member

    async def delete(self, member: Member) -> None:
        self._members.pop(member.id, None)
