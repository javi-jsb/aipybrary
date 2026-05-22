"""White-box tests for SqlModelMemberRepository's IntegrityError handling.

Happy-path behaviour is covered end-to-end in test_member_api.py against Postgres.
These tests isolate the branch that must not mislabel an unrelated IntegrityError.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.members.domain.member_model import Member, MemberUpdate
from app.members.infrastructure.sql_member_repository import SqlModelMemberRepository

_OTHER_VIOLATION = Exception('null value in column "full_name" violates not-null constraint')


class _StubSession:
    def __init__(self, error: Exception) -> None:
        self._error = error
        self.rolled_back = False

    def add(self, _obj: object) -> None:
        pass

    async def flush(self) -> None:
        raise IntegrityError("stmt", {}, self._error)

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, _obj: object) -> None:  # pragma: no cover - never reached
        pass


def _repo(error: Exception) -> tuple[SqlModelMemberRepository, _StubSession]:
    session = _StubSession(error)
    return SqlModelMemberRepository(session), session  # type: ignore[arg-type]


async def test_create_reraises_unrelated_integrity_error() -> None:
    repo, session = _repo(_OTHER_VIOLATION)
    member = Member(full_name="A", user_id=uuid.uuid4())
    with pytest.raises(IntegrityError):
        await repo.create(member)
    assert session.rolled_back is False  # create does not rollback on its own


async def test_update_reraises_unrelated_integrity_error() -> None:
    repo, _ = _repo(_OTHER_VIOLATION)
    member = Member(full_name="A", user_id=uuid.uuid4())
    with pytest.raises(IntegrityError):
        await repo.update(member, MemberUpdate(full_name="B"))
