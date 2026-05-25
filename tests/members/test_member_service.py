import uuid

import pytest

from app.core.sorting import SortOrder
from app.members.application.member_service import MemberService
from app.members.domain.member_exceptions import DuplicateEmailError
from app.members.domain.member_model import (
    MemberCreate,
    MemberStatus,
    MemberUpdate,
    SortBy,
)
from app.members.domain.member_repository import MemberRepository
from app.users.domain.user_exceptions import DuplicateEmailError as UserDuplicateEmailError
from app.users.domain.user_model import UserRole
from tests.fakes.member_fakes import FakeMemberRepository
from tests.fakes.user_fakes import FakeUserRepository


def _make_service() -> tuple[MemberService, FakeUserRepository, FakeMemberRepository]:
    user_repo = FakeUserRepository()
    member_repo = FakeMemberRepository(user_repo)
    return MemberService(user_repo, member_repo), user_repo, member_repo


async def test_create_member_provisions_user_and_member() -> None:
    service, user_repo, _ = _make_service()
    response = await service.create(MemberCreate(full_name="Ada", email="ada@example.com"))
    assert response.full_name == "Ada"
    assert response.email == "ada@example.com"
    assert response.id is not None
    assert response.initial_password != ""
    # A member-role user was created in the user repo
    user = await user_repo.get_by_email("ada@example.com")
    assert user is not None
    assert user.role == UserRole.member


async def test_create_member_raises_duplicate_email_if_user_email_taken() -> None:
    service, user_repo, _ = _make_service()
    await service.create(MemberCreate(full_name="Ada", email="dup@example.com"))
    with pytest.raises(DuplicateEmailError):
        await service.create(MemberCreate(full_name="Alan", email="dup@example.com"))


async def test_get_by_id_existing() -> None:
    service, _, _ = _make_service()
    created = await service.create(MemberCreate(full_name="Ada", email="ada@example.com"))
    result = await service.get_by_id(created.id)
    assert result is not None
    member, email = result
    assert member.id == created.id
    assert email == "ada@example.com"


async def test_get_by_id_missing() -> None:
    service, _, _ = _make_service()
    assert await service.get_by_id(uuid.uuid4()) is None


async def test_get_filtered_empty() -> None:
    service, _, _ = _make_service()
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.items == []
    assert result.total == 0
    assert result.pages == 0


async def test_get_filtered_with_members() -> None:
    service, _, _ = _make_service()
    await service.create(MemberCreate(full_name="A", email="a@example.com"))
    await service.create(MemberCreate(full_name="B", email="b@example.com"))
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert len(result.items) == 2
    assert result.total == 2
    assert result.pages == 1


async def test_get_filtered_pagination() -> None:
    service, _, _ = _make_service()
    for i in range(5):
        await service.create(MemberCreate(full_name=f"M{i}", email=f"m{i}@example.com"))
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 3)
    assert len(result.items) == 3
    assert result.total == 5
    assert result.pages == 2


async def test_get_filtered_by_status() -> None:
    service, _, _ = _make_service()
    await service.create(MemberCreate(full_name="Active", email="active@example.com"))
    await service.create(
        MemberCreate(full_name="Suspended", email="suspended@example.com", status=MemberStatus.suspended)
    )
    result = await service.get_filtered(None, None, MemberStatus.suspended, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.total == 1
    assert result.items[0].status is MemberStatus.suspended


async def test_update_existing() -> None:
    service, _, _ = _make_service()
    created = await service.create(MemberCreate(full_name="Old", email="old@example.com"))
    result = await service.update(created.id, MemberUpdate(full_name="New"))
    assert result is not None
    member, email = result
    assert member.full_name == "New"
    assert email == "old@example.com"


async def test_update_missing() -> None:
    service, _, _ = _make_service()
    assert await service.update(uuid.uuid4(), MemberUpdate(full_name="X")) is None


async def test_delete_existing() -> None:
    service, _, _ = _make_service()
    created = await service.create(MemberCreate(full_name="Bye", email="bye@example.com"))
    assert await service.delete(created.id) is True
    assert await service.get_by_id(created.id) is None


async def test_delete_missing() -> None:
    service, _, _ = _make_service()
    assert await service.delete(uuid.uuid4()) is False


def test_repository_contract_enforced() -> None:
    class Incomplete(MemberRepository):
        pass

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


async def test_create_member_wraps_user_duplicate_email() -> None:
    """UserDuplicateEmailError from the user repo is re-raised as DuplicateEmailError."""
    user_repo = FakeUserRepository()
    member_repo = FakeMemberRepository(user_repo)

    class _RaisingUserRepo(FakeUserRepository):
        async def create(self, user):  # type: ignore[override]
            raise UserDuplicateEmailError

    service = MemberService(_RaisingUserRepo(), member_repo)
    with pytest.raises(DuplicateEmailError):
        await service.create(MemberCreate(full_name="A", email="a@example.com"))
