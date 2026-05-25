import uuid
from abc import ABC, abstractmethod

from app.users.domain.user_model import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...
