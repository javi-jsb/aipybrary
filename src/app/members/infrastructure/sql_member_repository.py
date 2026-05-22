import uuid

from sqlalchemy import func
from sqlalchemy import select as sa_select
from sqlalchemy.exc import IntegrityError
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.sorting import SortOrder
from app.members.domain.member_model import (
    Member,
    MemberStatus,
    MemberUpdate,
    SortBy,
)
from app.members.domain.member_repository import MemberRepository
from app.users.domain.user_model import User


class SqlModelMemberRepository(MemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, member: Member) -> Member:
        self._session.add(member)
        await self._session.commit()
        await self._session.refresh(member)
        return member

    async def get_by_id(self, member_id: uuid.UUID) -> Member | None:
        return await self._session.get(Member, member_id)

    async def get_by_id_with_email(self, member_id: uuid.UUID) -> tuple[Member, str] | None:
        stmt = sa_select(Member, User.email).join(User, Member.user_id == User.id).where(Member.id == member_id)
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return row[0], row[1]

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
        conditions = []
        if full_name:
            conditions.append(col(Member.full_name).ilike(f"%{full_name}%"))
        if email:
            conditions.append(User.email.ilike(f"%{email}%"))
        if status is not None:
            conditions.append(col(Member.status) == status)

        count_stmt = sa_select(func.count(Member.id)).join(User, Member.user_id == User.id)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total: int = (await self._session.execute(count_stmt)).scalar_one()

        if sort_by == SortBy.email:
            sort_col = User.email
        else:
            sort_col = getattr(Member, sort_by.value)
        ordered = sort_col.desc() if order == SortOrder.desc else sort_col.asc()

        stmt = sa_select(Member, User.email).join(User, Member.user_id == User.id)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ordered).offset((page - 1) * size).limit(size)

        rows = (await self._session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows], total

    async def update(self, member: Member, data: MemberUpdate) -> Member:
        member.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._session.add(member)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        await self._session.refresh(member)
        return member

    async def delete(self, member: Member) -> None:
        await self._session.delete(member)
        await self._session.commit()
