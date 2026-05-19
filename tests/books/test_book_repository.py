"""White-box tests for SqlModelBookRepository's IntegrityError handling.

The happy path and the real duplicate-isbn 409 are covered end-to-end in
test_book_api.py against Postgres. These tests isolate the branch that must
*not* mislabel an unrelated IntegrityError as a duplicate isbn.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.books.domain.book_exceptions import DuplicateIsbnError
from app.books.domain.book_model import Book, BookCreate, BookUpdate
from app.books.infrastructure.sql_book_repository import SqlModelBookRepository

_ISBN_VIOLATION = Exception('duplicate key value violates unique constraint "uq_books_isbn"')
_OTHER_VIOLATION = Exception('null value in column "title" violates not-null constraint')


class _StubSession:
    def __init__(self, error: Exception) -> None:
        self._error = error
        self.rolled_back = False

    def add(self, _obj: object) -> None:
        pass

    async def commit(self) -> None:
        raise IntegrityError("stmt", {}, self._error)

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, _obj: object) -> None:  # pragma: no cover - never reached
        pass


def _repo(error: Exception) -> tuple[SqlModelBookRepository, _StubSession]:
    session = _StubSession(error)
    return SqlModelBookRepository(session), session  # type: ignore[arg-type]


async def test_create_maps_isbn_constraint_to_domain_error() -> None:
    repo, session = _repo(_ISBN_VIOLATION)
    with pytest.raises(DuplicateIsbnError):
        await repo.create(BookCreate(title="A", author="B", isbn="9780060934347"))
    assert session.rolled_back is True


async def test_create_reraises_unrelated_integrity_error() -> None:
    repo, session = _repo(_OTHER_VIOLATION)
    with pytest.raises(IntegrityError):
        await repo.create(BookCreate(title="A", author="B"))
    assert session.rolled_back is True


async def test_update_maps_isbn_constraint_to_domain_error() -> None:
    repo, _ = _repo(_ISBN_VIOLATION)
    book = Book(title="A", author="B")
    with pytest.raises(DuplicateIsbnError):
        await repo.update(book, BookUpdate(isbn="9780060934347"))


async def test_update_reraises_unrelated_integrity_error() -> None:
    repo, _ = _repo(_OTHER_VIOLATION)
    book = Book(title="A", author="B")
    with pytest.raises(IntegrityError):
        await repo.update(book, BookUpdate(title="C"))
