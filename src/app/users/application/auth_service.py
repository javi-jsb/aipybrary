from app.config import settings
from app.core.security import dummy_verify_password, encode_token, verify_password
from app.users.domain.user_exceptions import InactiveUserError, InvalidCredentialsError
from app.users.domain.user_repository import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def authenticate(self, email: str, password: str) -> str:
        user = await self._repository.get_by_email(email.strip().lower())
        if user is None:
            dummy_verify_password(password)
            raise InvalidCredentialsError
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        if not user.is_active:
            raise InactiveUserError
        return encode_token(
            str(user.id),
            user.role,
            settings.JWT_SECRET,
            settings.JWT_ALGORITHM,
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        )
