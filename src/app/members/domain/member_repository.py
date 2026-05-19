import uuid
from abc import ABC, abstractmethod

from app.members.domain.member_model import (
    Member,
    MemberCreate,
    MemberUpdate,
    SortBy,
    SortOrder,
)


class MemberRepository(ABC):
    @abstractmethod
    async def create(self, data: MemberCreate) -> Member: ...

    @abstractmethod
    async def get_by_id(self, member_id: uuid.UUID) -> Member | None: ...

    @abstractmethod
    async def get_filtered(
        self,
        full_name: str | None,
        email: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[Member], int]: ...

    @abstractmethod
    async def update(self, member: Member, data: MemberUpdate) -> Member: ...

    @abstractmethod
    async def delete(self, member: Member) -> None: ...
