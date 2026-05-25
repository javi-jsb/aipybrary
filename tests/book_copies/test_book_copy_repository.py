"""White-box tests for SqlModelBookCopyRepository's IntegrityError handling.

The happy path and the real duplicate-barcode 409 are covered end-to-end in
test_book_copy_api.py against Postgres. These tests isolate the branch that
must *not* mislabel an unrelated IntegrityError as a duplicate barcode.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.book_copies.domain.book_copy_exceptions import DuplicateBarcodeError
from app.book_copies.domain.book_copy_model import BookCopy, BookCopyCreate, BookCopyUpdate
from app.book_copies.infrastructure.sql_book_copy_repository import SqlModelBookCopyRepository

_BARCODE_VIOLATION = Exception('duplicate key value violates unique constraint "uq_book_copies_barcode"')
_OTHER_VIOLATION = Exception('null value in column "barcode" violates not-null constraint')


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


def _repo(error: Exception) -> tuple[SqlModelBookCopyRepository, _StubSession]:
    session = _StubSession(error)
    return SqlModelBookCopyRepository(session), session  # type: ignore[arg-type]


async def test_create_maps_barcode_constraint_to_domain_error() -> None:
    repo, session = _repo(_BARCODE_VIOLATION)
    with pytest.raises(DuplicateBarcodeError):
        await repo.create(BookCopyCreate(book_id=uuid.uuid4(), barcode="ABC"))
    assert session.rolled_back is True


async def test_create_reraises_unrelated_integrity_error() -> None:
    repo, session = _repo(_OTHER_VIOLATION)
    with pytest.raises(IntegrityError):
        await repo.create(BookCopyCreate(book_id=uuid.uuid4(), barcode="ABC"))
    assert session.rolled_back is True


async def test_update_maps_barcode_constraint_to_domain_error() -> None:
    repo, _ = _repo(_BARCODE_VIOLATION)
    copy = BookCopy(book_id=uuid.uuid4(), barcode="OLD")
    with pytest.raises(DuplicateBarcodeError):
        await repo.update(copy, BookCopyUpdate(barcode="NEW"))


async def test_update_reraises_unrelated_integrity_error() -> None:
    repo, _ = _repo(_OTHER_VIOLATION)
    copy = BookCopy(book_id=uuid.uuid4(), barcode="OLD")
    with pytest.raises(IntegrityError):
        await repo.update(copy, BookCopyUpdate(barcode="NEW"))


class _CountSession:
    """Minimal stub for SqlModelBookCopyRepository.count_by_book_id."""

    def __init__(self, count: int) -> None:
        self._count = count

    async def exec(self, _stmt: object) -> "_CountResult":
        return _CountResult(self._count)


class _CountResult:
    def __init__(self, count: int) -> None:
        self._count = count

    def one(self) -> int:
        return self._count


async def test_count_by_book_id_returns_session_count() -> None:
    session = _CountSession(7)
    repo = SqlModelBookCopyRepository(session)  # type: ignore[arg-type]
    assert await repo.count_by_book_id(uuid.uuid4()) == 7
