import uuid

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import is_constraint_violated
from app.members.domain.member_exceptions import DuplicateEmailError
from app.members.domain.member_model import (
    EMAIL_CONSTRAINT,
    Member,
    MemberCreate,
    MemberStatus,
    MemberUpdate,
    SortBy,
    SortOrder,
)
from app.members.domain.member_repository import MemberRepository


class SqlModelMemberRepository(MemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: MemberCreate) -> Member:
        member = Member.model_validate(data)
        self._session.add(member)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if is_constraint_violated(exc, EMAIL_CONSTRAINT):
                raise DuplicateEmailError from exc
            raise
        await self._session.refresh(member)
        return member

    async def get_by_id(self, member_id: uuid.UUID) -> Member | None:
        return await self._session.get(Member, member_id)

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
        conditions = []
        if full_name:
            conditions.append(col(Member.full_name).ilike(f"%{full_name}%"))
        if email:
            conditions.append(col(Member.email).ilike(f"%{email}%"))
        if status is not None:
            conditions.append(col(Member.status) == status)

        sort_attr = getattr(Member, sort_by.value)
        ordered = sort_attr.desc() if order == SortOrder.desc else sort_attr.asc()

        count_stmt = select(func.count(col(Member.id)))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total: int = (await self._session.exec(count_stmt)).one()

        stmt = select(Member)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ordered).offset((page - 1) * size).limit(size)
        result = await self._session.exec(stmt)
        return list(result.all()), total

    async def update(self, member: Member, data: MemberUpdate) -> Member:
        member.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._session.add(member)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if is_constraint_violated(exc, EMAIL_CONSTRAINT):
                raise DuplicateEmailError from exc
            raise
        await self._session.refresh(member)
        return member

    async def delete(self, member: Member) -> None:
        await self._session.delete(member)
        await self._session.commit()
