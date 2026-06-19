import uuid
from abc import ABC, abstractmethod

from app.core.sorting import SortOrder
from app.members.domain.member_model import (
    Member,
    MemberStatus,
    MemberUpdate,
    SortBy,
)


class MemberRepository(ABC):
    @abstractmethod
    async def create(self, member: Member) -> Member: ...

    @abstractmethod
    async def get_by_id(self, member_id: uuid.UUID) -> Member | None: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> Member | None: ...

    @abstractmethod
    async def get_by_id_with_email(self, member_id: uuid.UUID) -> tuple[Member, str] | None: ...

    @abstractmethod
    async def get_filtered(
        self,
        full_name: str | None,
        email: str | None,
        status: MemberStatus | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[tuple[Member, str]], int]: ...

    @abstractmethod
    async def update(self, member: Member, data: MemberUpdate) -> Member: ...

    @abstractmethod
    async def delete(self, member: Member) -> None: ...
