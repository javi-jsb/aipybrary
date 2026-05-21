import uuid

import pytest

from app.book_copies.application.book_copy_service import BookCopyService
from app.book_copies.domain.book_copy_exceptions import BookCopyBookNotFoundError
from app.book_copies.domain.book_copy_model import (
    BookCopy,
    BookCopyCreate,
    BookCopyUpdate,
    SortBy,
    SortOrder,
)
from app.book_copies.domain.book_copy_repository import BookCopyRepository
from app.books.domain.book_model import Book, BookCreate, BookUpdate
from app.books.domain.book_model import SortBy as BookSortBy
from app.books.domain.book_model import SortOrder as BookSortOrder
from app.books.domain.book_repository import BookRepository, BookWithCounts


class FakeBookRepository(BookRepository):
    def __init__(self) -> None:
        self._books: dict[uuid.UUID, Book] = {}

    def add(self, book: Book) -> None:
        self._books[book.id] = book

    async def create(self, data: BookCreate) -> Book:
        book = Book.model_validate(data)
        self._books[book.id] = book
        return book

    async def get_by_id(self, book_id: uuid.UUID) -> BookWithCounts | None:
        book = self._books.get(book_id)
        if book is None:
            return None
        return BookWithCounts(book, 0, 0)

    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: BookSortBy,
        order: BookSortOrder,
        page: int,
        size: int,
    ) -> tuple[list[BookWithCounts], int]:  # pragma: no cover - not exercised here
        return [], 0

    async def update(self, book: Book, data: BookUpdate) -> BookWithCounts:  # pragma: no cover - not exercised here
        return BookWithCounts(book, 0, 0)

    async def delete(self, book: Book) -> None:  # pragma: no cover - not exercised here
        self._books.pop(book.id, None)


class FakeBookCopyRepository(BookCopyRepository):
    def __init__(self) -> None:
        self._copies: dict[uuid.UUID, BookCopy] = {}

    async def create(self, data: BookCopyCreate) -> BookCopy:
        copy = BookCopy.model_validate(data)
        self._copies[copy.id] = copy
        return copy

    async def get_by_id(self, copy_id: uuid.UUID) -> BookCopy | None:
        return self._copies.get(copy_id)

    async def get_filtered(
        self,
        book_id: uuid.UUID | None,
        barcode: str | None,
        location: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[BookCopy], int]:
        items = list(self._copies.values())
        if book_id is not None:
            items = [c for c in items if c.book_id == book_id]
        if barcode:
            items = [c for c in items if barcode.lower() in c.barcode.lower()]
        if location:
            items = [c for c in items if c.location and location.lower() in c.location.lower()]
        total = len(items)
        offset = (page - 1) * size
        return items[offset : offset + size], total

    async def update(self, copy: BookCopy, data: BookCopyUpdate) -> BookCopy:
        copy.sqlmodel_update(data.model_dump(exclude_unset=True))
        return copy

    async def delete(self, copy: BookCopy) -> None:
        self._copies.pop(copy.id, None)

    async def count_by_book_id(self, book_id: uuid.UUID) -> int:
        return sum(1 for c in self._copies.values() if c.book_id == book_id)


def _make_service() -> tuple[BookCopyService, FakeBookCopyRepository, FakeBookRepository]:
    copy_repo = FakeBookCopyRepository()
    book_repo = FakeBookRepository()
    return BookCopyService(copy_repo, book_repo), copy_repo, book_repo


async def test_create_delegates_when_book_exists() -> None:
    service, _, book_repo = _make_service()
    book = Book(title="T", author="A")
    book_repo.add(book)
    copy = await service.create(BookCopyCreate(book_id=book.id, barcode="ABC"))
    assert copy.book_id == book.id
    assert copy.barcode == "ABC"


async def test_create_raises_when_book_missing() -> None:
    service, _, _ = _make_service()
    with pytest.raises(BookCopyBookNotFoundError):
        await service.create(BookCopyCreate(book_id=uuid.uuid4(), barcode="ABC"))


async def test_get_by_id_existing() -> None:
    service, _, book_repo = _make_service()
    book = Book(title="T", author="A")
    book_repo.add(book)
    created = await service.create(BookCopyCreate(book_id=book.id, barcode="ABC"))
    found = await service.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id


async def test_get_by_id_missing() -> None:
    service, _, _ = _make_service()
    assert await service.get_by_id(uuid.uuid4()) is None


async def test_get_filtered_empty() -> None:
    service, _, _ = _make_service()
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.items == []
    assert result.total == 0
    assert result.pages == 0


async def test_get_filtered_pagination_and_filters() -> None:
    service, _, book_repo = _make_service()
    book = Book(title="T", author="A")
    book_repo.add(book)
    for i in range(5):
        await service.create(BookCopyCreate(book_id=book.id, barcode=f"BC-{i}"))
    result = await service.get_filtered(book.id, None, None, SortBy.created_at, SortOrder.desc, 1, 3)
    assert len(result.items) == 3
    assert result.total == 5
    assert result.pages == 2


async def test_update_existing() -> None:
    service, _, book_repo = _make_service()
    book = Book(title="T", author="A")
    book_repo.add(book)
    created = await service.create(BookCopyCreate(book_id=book.id, barcode="OLD"))
    updated = await service.update(created.id, BookCopyUpdate(barcode="NEW"))
    assert updated is not None
    assert updated.barcode == "NEW"


async def test_update_missing() -> None:
    service, _, _ = _make_service()
    assert await service.update(uuid.uuid4(), BookCopyUpdate(barcode="X")) is None


async def test_delete_existing() -> None:
    service, _, book_repo = _make_service()
    book = Book(title="T", author="A")
    book_repo.add(book)
    created = await service.create(BookCopyCreate(book_id=book.id, barcode="X"))
    assert await service.delete(created.id) is True
    assert await service.get_by_id(created.id) is None


async def test_delete_missing() -> None:
    service, _, _ = _make_service()
    assert await service.delete(uuid.uuid4()) is False


def test_repository_contract_enforced() -> None:
    class Incomplete(BookCopyRepository):
        pass

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]
