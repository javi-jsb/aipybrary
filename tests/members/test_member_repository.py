"""White-box tests for SqlModelMemberRepository's IntegrityError handling.

Happy-path behaviour is covered end-to-end in test_member_api.py against Postgres.
These tests confirm that an unrelated IntegrityError propagates unchanged rather
than being swallowed or mislabelled.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.members.domain.member_exceptions import MemberHasLoansError
from app.members.domain.member_model import Member, MemberUpdate
from app.members.infrastructure.sql_member_repository import SqlModelMemberRepository

_OTHER_VIOLATION = Exception('null value in column "full_name" violates not-null constraint')
_LOANS_FK_VIOLATION = Exception(
    'update or delete on table "members" violates foreign key constraint "fk_loans_member_id_members" on table "loans"'
)


class _StubSession:
    def add(self, _obj: object) -> None:
        pass

    async def flush(self) -> None:
        raise IntegrityError("stmt", {}, _OTHER_VIOLATION)

    async def refresh(self, _obj: object) -> None:  # pragma: no cover - never reached
        pass


def _repo() -> SqlModelMemberRepository:
    return SqlModelMemberRepository(_StubSession())  # type: ignore[arg-type]


async def test_create_reraises_unrelated_integrity_error() -> None:
    member = Member(full_name="A", user_id=uuid.uuid4())
    with pytest.raises(IntegrityError):
        await _repo().create(member)


async def test_update_reraises_unrelated_integrity_error() -> None:
    member = Member(full_name="A", user_id=uuid.uuid4())
    with pytest.raises(IntegrityError):
        await _repo().update(member, MemberUpdate(full_name="B"))


class _DeleteStubSession:
    def __init__(self, error: Exception) -> None:
        self._error = error
        self.rolled_back = False

    async def delete(self, _obj: object) -> None:
        pass

    async def flush(self) -> None:
        raise IntegrityError("stmt", {}, self._error)

    async def rollback(self) -> None:
        self.rolled_back = True


async def test_delete_maps_loans_fk_to_domain_error() -> None:
    session = _DeleteStubSession(_LOANS_FK_VIOLATION)
    repo = SqlModelMemberRepository(session)  # type: ignore[arg-type]
    member = Member(full_name="A", user_id=uuid.uuid4())
    with pytest.raises(MemberHasLoansError):
        await repo.delete(member)
    assert session.rolled_back is True


async def test_delete_reraises_unrelated_integrity_error() -> None:
    session = _DeleteStubSession(_OTHER_VIOLATION)
    repo = SqlModelMemberRepository(session)  # type: ignore[arg-type]
    member = Member(full_name="A", user_id=uuid.uuid4())
    with pytest.raises(IntegrityError):
        await repo.delete(member)
    assert session.rolled_back is True
