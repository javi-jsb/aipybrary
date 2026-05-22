"""Tests for the member provisioning flow introduced by the authentication change.

POST /members creates a member-role User, returns a one-time initial_password,
and rejects duplicate emails with 409.
"""

import uuid

from httpx import AsyncClient

from app.users.domain.user_model import UserRole


async def _create_member(client: AsyncClient, **kwargs: object) -> dict:
    payload = {"full_name": "Test Member", "email": f"member-{uuid.uuid4()}@example.com", **kwargs}
    response = await client.post("/members", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_member_returns_initial_password(client: AsyncClient) -> None:
    response = await client.post("/members", json={"full_name": "Ada", "email": "ada@example.com"})
    assert response.status_code == 201
    data = response.json()
    assert "initial_password" in data
    assert data["initial_password"] != ""


async def test_create_member_provisions_linked_user(client: AsyncClient, session) -> None:
    response = await client.post("/members", json={"full_name": "Alan", "email": "alan@example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alan@example.com"

    from sqlmodel import select

    from app.users.domain.user_model import User

    user = (await session.exec(select(User).where(User.email == "alan@example.com"))).first()
    assert user is not None
    assert user.role == UserRole.member
    assert user.is_active is True


async def test_create_member_initial_password_not_returned_again(client: AsyncClient) -> None:
    member = await _create_member(client)
    response = await client.get(f"/members/{member['id']}")
    assert response.status_code == 200
    assert "initial_password" not in response.json()


async def test_create_member_duplicate_email_returns_409(client: AsyncClient) -> None:
    await _create_member(client, email="dup@example.com")
    response = await client.post("/members", json={"full_name": "Other", "email": "dup@example.com"})
    assert response.status_code == 409


async def test_create_member_duplicate_email_no_orphan_user(client: AsyncClient, session) -> None:
    await _create_member(client, email="dup2@example.com")
    response = await client.post("/members", json={"full_name": "Other", "email": "dup2@example.com"})
    assert response.status_code == 409

    from sqlmodel import select

    from app.users.domain.user_model import User

    users = (await session.exec(select(User).where(User.email == "dup2@example.com"))).all()
    assert len(users) == 1  # only the first user was created
