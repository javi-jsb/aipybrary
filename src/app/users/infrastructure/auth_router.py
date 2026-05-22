import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.core.security import decode_token
from app.database import get_session
from app.users.application.auth_service import AuthService
from app.users.domain.user_exceptions import InactiveUserError, InvalidCredentialsError
from app.users.domain.user_model import User, UserPublic
from app.users.infrastructure.sql_user_repository import SqlModelUserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    try:
        payload = decode_token(token, settings.JWT_SECRET, settings.JWT_ALGORITHM)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _CREDENTIALS_EXCEPTION from None
    repo = SqlModelUserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION
    return user


def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> AuthService:
    return AuthService(SqlModelUserRepository(session))


ServiceDep = Annotated[AuthService, Depends(_get_service)]


@router.post("/login")
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], service: ServiceDep) -> dict:
    try:
        token = await service.authenticate(form.username, form.password)
    except (InvalidCredentialsError, InactiveUserError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(current_user)
