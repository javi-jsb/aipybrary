import uuid

from app.core.security import generate_password, hash_password
from app.core.sorting import SortOrder
from app.members.domain.member_exceptions import DuplicateEmailError
from app.members.domain.member_model import (
    Member,
    MemberCreate,
    MemberCreateResponse,
    MemberListResponse,
    MemberPublic,
    MemberStatus,
    MemberUpdate,
    SortBy,
)
from app.members.domain.member_repository import MemberRepository
from app.users.domain.user_exceptions import DuplicateEmailError as UserDuplicateEmailError
from app.users.domain.user_model import User, UserRole
from app.users.domain.user_repository import UserRepository


class MemberService:
    def __init__(self, user_repository: UserRepository, member_repository: MemberRepository) -> None:
        self._user_repository = user_repository
        self._member_repository = member_repository

    async def create(self, data: MemberCreate) -> MemberCreateResponse:
        password = generate_password()
        user = User(email=data.email, password_hash=hash_password(password), role=UserRole.member, is_active=True)
        try:
            created_user = await self._user_repository.create(user)
        except UserDuplicateEmailError:
            raise DuplicateEmailError from None
        member = Member(full_name=data.full_name, status=data.status, user_id=created_user.id)
        created_member = await self._member_repository.create(member)
        return MemberCreateResponse(
            id=created_member.id,
            full_name=created_member.full_name,
            email=data.email,
            status=created_member.status,
            created_at=created_member.created_at,
            updated_at=created_member.updated_at,
            initial_password=password,
        )

    async def get_by_id(self, member_id: uuid.UUID) -> tuple[Member, str] | None:
        return await self._member_repository.get_by_id_with_email(member_id)

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
        rows, total = await self._member_repository.get_filtered(full_name, email, status, sort_by, order, page, size)
        items = [MemberPublic.from_member(member, email) for member, email in rows]
        return MemberListResponse(items=items, total=total, page=page, size=size)

    async def update(self, member_id: uuid.UUID, data: MemberUpdate) -> tuple[Member, str] | None:
        result = await self._member_repository.get_by_id_with_email(member_id)
        if result is None:
            return None
        member, email = result
        updated = await self._member_repository.update(member, data)
        return updated, email

    async def delete(self, member_id: uuid.UUID) -> bool:
        member = await self._member_repository.get_by_id(member_id)
        if member is None:
            return False
        await self._member_repository.delete(member)
        return True
