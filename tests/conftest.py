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
from app.members.domain.member_model import Member, MemberStatus
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


def _fake_user(role: UserRole) -> User:
    return User(email=f"{role.value}@test.example", password_hash="fake-hash", role=role, is_active=True)


def _session_override(session: AsyncSession):
    async def _override_get_session() -> AsyncGenerator[AsyncSession]:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return _override_get_session


async def _role_client(session: AsyncSession, role: UserRole) -> AsyncGenerator[AsyncClient]:
    app.dependency_overrides[get_session] = _session_override(session)
    app.dependency_overrides[get_current_user] = lambda: _fake_user(role)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Authenticated client — get_current_user returns a canned staff user."""
    async for c in _role_client(session, UserRole.staff):
        yield c


@pytest.fixture
async def admin_client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Authenticated client whose current user is a canned admin."""
    async for c in _role_client(session, UserRole.admin):
        yield c


@pytest.fixture
async def member_client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Authenticated client whose current user is a canned member (no linked Member row).

    Use for role-only allow/deny checks. For ownership/scoping tests where the
    member must own a resource, use `member_account` instead.
    """
    async for c in _role_client(session, UserRole.member):
        yield c


@pytest.fixture
async def member_account(session: AsyncSession) -> AsyncGenerator[tuple[AsyncClient, Member]]:
    """A member-role client whose user is linked to a persisted Member row.

    Yields ``(client, member)`` so ownership/scoping tests can assert a member
    acts on their own record. Rows are flushed (not committed) so they are visible
    within the request's session; the per-request override commits.
    """
    user = User(email="owner@test.example", password_hash="fake-hash", role=UserRole.member, is_active=True)
    session.add(user)
    await session.flush()
    member = Member(full_name="Owner Member", status=MemberStatus.active, user_id=user.id)
    session.add(member)
    await session.flush()

    app.dependency_overrides[get_session] = _session_override(session)
    app.dependency_overrides[get_current_user] = lambda: user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, member
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
