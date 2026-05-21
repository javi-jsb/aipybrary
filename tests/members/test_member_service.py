import uuid

import pytest

from app.members.application.member_service import MemberService
from app.members.domain.member_model import (
    MemberCreate,
    MemberStatus,
    MemberUpdate,
    SortBy,
    SortOrder,
)
from app.members.domain.member_repository import MemberRepository
from tests.fakes.member_fakes import FakeMemberRepository


def _make_service() -> MemberService:
    return MemberService(FakeMemberRepository())


async def test_create_member_delegates_to_repository() -> None:
    service = _make_service()
    member = await service.create(MemberCreate(full_name="Ada", email="ada@example.com"))
    assert member.full_name == "Ada"
    assert member.email == "ada@example.com"
    assert member.id is not None


async def test_get_by_id_existing() -> None:
    service = _make_service()
    created = await service.create(MemberCreate(full_name="Ada", email="ada@example.com"))
    found = await service.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id


async def test_get_by_id_missing() -> None:
    service = _make_service()
    assert await service.get_by_id(uuid.uuid4()) is None


async def test_get_filtered_empty() -> None:
    service = _make_service()
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.items == []
    assert result.total == 0
    assert result.pages == 0


async def test_get_filtered_with_members() -> None:
    service = _make_service()
    await service.create(MemberCreate(full_name="A", email="a@example.com"))
    await service.create(MemberCreate(full_name="B", email="b@example.com"))
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert len(result.items) == 2
    assert result.total == 2
    assert result.pages == 1


async def test_get_filtered_pagination() -> None:
    service = _make_service()
    for i in range(5):
        await service.create(MemberCreate(full_name=f"M{i}", email=f"m{i}@example.com"))
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 3)
    assert len(result.items) == 3
    assert result.total == 5
    assert result.pages == 2


async def test_get_filtered_by_status() -> None:
    service = _make_service()
    await service.create(MemberCreate(full_name="Active", email="active@example.com"))
    await service.create(
        MemberCreate(
            full_name="Suspended",
            email="suspended@example.com",
            status=MemberStatus.suspended,
        )
    )
    result = await service.get_filtered(None, None, MemberStatus.suspended, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.total == 1
    assert result.items[0].status is MemberStatus.suspended


async def test_update_existing() -> None:
    service = _make_service()
    created = await service.create(MemberCreate(full_name="Old", email="old@example.com"))
    updated = await service.update(created.id, MemberUpdate(full_name="New"))
    assert updated is not None
    assert updated.full_name == "New"
    assert updated.email == "old@example.com"


async def test_update_missing() -> None:
    service = _make_service()
    assert await service.update(uuid.uuid4(), MemberUpdate(full_name="X")) is None


async def test_delete_existing() -> None:
    service = _make_service()
    created = await service.create(MemberCreate(full_name="Bye", email="bye@example.com"))
    assert await service.delete(created.id) is True
    assert await service.get_by_id(created.id) is None


async def test_delete_missing() -> None:
    service = _make_service()
    assert await service.delete(uuid.uuid4()) is False


def test_repository_contract_enforced() -> None:
    class Incomplete(MemberRepository):
        pass

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]
