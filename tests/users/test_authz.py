"""Unit tests for the authorization primitives, exercised in isolation.

The dependency functions are plain async callables, so we invoke them directly
with constructed arguments rather than through the HTTP stack (the per-endpoint
matrix is covered by tests/test_authorization.py).
"""

import uuid

import pytest
from fastapi import HTTPException

from app.members.domain.member_model import Member, MemberStatus
from app.users.domain.user_model import User, UserRole
from app.users.infrastructure.authz import (
    require_role,
    require_self_or_staff,
    resolve_own_member,
)
from tests.fakes.member_fakes import FakeMemberRepository


def _user(role: UserRole) -> User:
    return User(email=f"{role.value}@test.example", password_hash="x", role=role, is_active=True)


def _member_for(user: User) -> Member:
    return Member(full_name="Owner", status=MemberStatus.active, user_id=user.id)


async def test_require_role_allows_listed_role() -> None:
    dep = require_role(UserRole.admin, UserRole.staff)
    user = _user(UserRole.staff)
    assert await dep(user) is user


async def test_require_role_forbids_unlisted_role() -> None:
    dep = require_role(UserRole.admin, UserRole.staff)
    with pytest.raises(HTTPException) as exc:
        await dep(_user(UserRole.member))
    assert exc.value.status_code == 403


async def test_resolve_own_member_returns_linked_member() -> None:
    user = _user(UserRole.member)
    member = _member_for(user)
    repo = FakeMemberRepository()
    repo.add(member)
    assert await resolve_own_member(user, repo) is member


async def test_resolve_own_member_without_link_is_forbidden() -> None:
    with pytest.raises(HTTPException) as exc:
        await resolve_own_member(_user(UserRole.member), FakeMemberRepository())
    assert exc.value.status_code == 403


async def test_require_self_or_staff_staff_bypasses_ownership() -> None:
    user = _user(UserRole.staff)
    # An empty repo proves staff never needs a linked member.
    out = await require_self_or_staff(uuid.uuid4(), user, FakeMemberRepository())
    assert out is user


async def test_require_self_or_staff_member_allows_own_id() -> None:
    user = _user(UserRole.member)
    member = _member_for(user)
    repo = FakeMemberRepository()
    repo.add(member)
    assert await require_self_or_staff(member.id, user, repo) is user


async def test_require_self_or_staff_member_forbidden_for_other_id() -> None:
    user = _user(UserRole.member)
    member = _member_for(user)
    repo = FakeMemberRepository()
    repo.add(member)
    with pytest.raises(HTTPException) as exc:
        await require_self_or_staff(uuid.uuid4(), user, repo)
    assert exc.value.status_code == 403
