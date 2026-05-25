from collections.abc import AsyncGenerator

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from alembic import command
from app.config import settings
from app.database import get_session
from app.main import app
from app.users.domain.user_model import User, UserRole
from app.users.infrastructure.auth_router import get_current_user

test_engine = create_async_engine(settings.test_database_url, echo=False)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.test_database_url)
    return cfg


@pytest.fixture(autouse=True)
def db_setup() -> None:
    command.upgrade(_alembic_config(), "head")
    yield  # type: ignore[misc]
    command.downgrade(_alembic_config(), "base")


@pytest.fixture
async def session(db_setup: None) -> AsyncGenerator[AsyncSession]:
    async with test_async_session() as session:
        yield session


def _fake_staff_user() -> User:
    return User(email="staff@test.example", password_hash="fake-hash", role=UserRole.staff, is_active=True)


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Authenticated client — get_current_user returns a canned staff user."""

    async def _override_get_session() -> AsyncGenerator[AsyncSession]:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[get_current_user] = _fake_staff_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Unauthenticated client — no get_current_user override; used to test the real auth flow."""

    async def _override_get_session() -> AsyncGenerator[AsyncSession]:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
