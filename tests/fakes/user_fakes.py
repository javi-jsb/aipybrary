import uuid

from app.users.domain.user_model import User
from app.users.domain.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[uuid.UUID, User] = {}

    def add(self, user: User) -> None:
        self._users[user.id] = user

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._users.get(user_id)

    async def create(self, user: User) -> User:
        if any(u.email == user.email for u in self._users.values()):
            from app.users.domain.user_exceptions import DuplicateEmailError

            raise DuplicateEmailError
        self._users[user.id] = user
        return user
