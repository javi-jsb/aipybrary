"""Tests that the auth gate protects all endpoints and keeps /health and /auth/login public."""

import uuid

from httpx import AsyncClient

from app.config import settings
from app.core.security import encode_token


async def test_health_is_public(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/health")
    assert response.status_code == 200


async def test_login_is_public(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/auth/login", data={"username": "x@x.com", "password": "x"})
    assert response.status_code == 401  # wrong creds, but NOT a 401 from the auth gate


async def test_books_requires_token(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/books")
    assert response.status_code == 401


async def test_members_requires_token(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/members")
    assert response.status_code == 401


async def test_book_copies_requires_token(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/book-copies")
    assert response.status_code == 401


async def test_loans_requires_token(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/loans")
    assert response.status_code == 401


async def test_tampered_token_returns_401(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/books", headers={"Authorization": "Bearer not.a.valid.token"})
    assert response.status_code == 401


async def test_token_for_nonexistent_user_returns_401(auth_client: AsyncClient) -> None:
    token = encode_token(
        str(uuid.uuid4()),
        "staff",
        settings.JWT_SECRET,
        settings.JWT_ALGORITHM,
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    response = await auth_client.get("/books", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
