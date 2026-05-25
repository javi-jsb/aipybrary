import uuid

from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import is_constraint_violated
from app.users.domain.user_exceptions import DuplicateEmailError
from app.users.domain.user_model import EMAIL_CONSTRAINT, User
from app.users.domain.user_repository import UserRepository


class SqlModelUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.exec(select(User).where(col(User.email) == email))
        return result.first()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def create(self, user: User) -> User:
        self._session.add(user)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            if is_constraint_violated(exc, EMAIL_CONSTRAINT):
                raise DuplicateEmailError from exc
            raise
        await self._session.refresh(user)
        return user
