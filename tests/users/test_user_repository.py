"""White-box test for SqlModelUserRepository's IntegrityError handling.

Happy-path and duplicate-email behaviour are covered end-to-end against Postgres
in test_member_provisioning.py. This isolates the branch that must re-raise an
IntegrityError unrelated to the email uniqueness constraint instead of
mislabelling it as DuplicateEmailError.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.users.domain.user_model import User, UserRole
from app.users.infrastructure.sql_user_repository import SqlModelUserRepository

_OTHER_VIOLATION = Exception('null value in column "password_hash" violates not-null constraint')


class _StubSession:
    def add(self, _obj: object) -> None:
        pass

    async def flush(self) -> None:
        raise IntegrityError("stmt", {}, _OTHER_VIOLATION)

    async def refresh(self, _obj: object) -> None:  # pragma: no cover - never reached
        pass


async def test_create_reraises_unrelated_integrity_error() -> None:
    repo = SqlModelUserRepository(_StubSession())  # type: ignore[arg-type]
    user = User(email="x@example.com", password_hash="h", role=UserRole.member)
    with pytest.raises(IntegrityError):
        await repo.create(user)
