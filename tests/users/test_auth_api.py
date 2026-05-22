"""Tests for POST /auth/login and GET /auth/me."""

from httpx import AsyncClient

from app.core.security import hash_password
from app.users.domain.user_model import User, UserRole


async def _create_user(
    session, email: str, password: str, role: UserRole = UserRole.staff, is_active: bool = True
) -> User:
    from app.users.infrastructure.sql_user_repository import SqlModelUserRepository

    repo = SqlModelUserRepository(session)
    user = User(email=email, password_hash=hash_password(password), role=role, is_active=is_active)
    return await repo.create(user)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


async def test_login_success(auth_client: AsyncClient, session) -> None:
    await _create_user(session, "admin@example.com", "password123")
    response = await auth_client.post("/auth/login", data={"username": "admin@example.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(auth_client: AsyncClient, session) -> None:
    await _create_user(session, "user@example.com", "correct")
    response = await auth_client.post("/auth/login", data={"username": "user@example.com", "password": "wrong"})
    assert response.status_code == 401


async def test_login_unknown_email(auth_client: AsyncClient, session) -> None:
    response = await auth_client.post("/auth/login", data={"username": "nobody@example.com", "password": "x"})
    assert response.status_code == 401


async def test_login_inactive_user(auth_client: AsyncClient, session) -> None:
    await _create_user(session, "inactive@example.com", "pass", is_active=False)
    response = await auth_client.post("/auth/login", data={"username": "inactive@example.com", "password": "pass"})
    assert response.status_code == 401


async def test_login_email_is_case_insensitive(auth_client: AsyncClient, session) -> None:
    await _create_user(session, "casetest@example.com", "password123")
    response = await auth_client.post(
        "/auth/login", data={"username": "  CaseTest@Example.COM  ", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


async def _login(auth_client: AsyncClient, email: str, password: str) -> str:
    response = await auth_client.post("/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]


async def test_get_me_authenticated(auth_client: AsyncClient, session) -> None:
    await _create_user(session, "me@example.com", "pass")
    token = await _login(auth_client, "me@example.com", "pass")
    response = await auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert "password_hash" not in data


async def test_get_me_unauthenticated(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/auth/me")
    assert response.status_code == 401
