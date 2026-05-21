import uuid

from app.books.application.book_service import BookService
from app.books.domain.book_model import BookCreate, BookUpdate, SortBy
from app.core.sorting import SortOrder
from tests.fakes.book_fakes import FakeBookRepository


def _make_service() -> tuple[BookService, FakeBookRepository]:
    repo = FakeBookRepository()
    return BookService(repo), repo


async def test_create_book() -> None:
    service, _ = _make_service()
    book = await service.create(BookCreate(title="Test", author="Author"))
    assert book.title == "Test"
    assert book.author == "Author"
    assert book.id is not None
    assert book.copies_total == 0
    assert book.copies_available == 0


async def test_get_by_id_existing() -> None:
    service, _ = _make_service()
    created = await service.create(BookCreate(title="Test", author="Author"))
    found = await service.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id


async def test_get_by_id_missing() -> None:
    service, _ = _make_service()
    result = await service.get_by_id(uuid.uuid4())
    assert result is None


async def test_get_by_id_includes_copies_total() -> None:
    service, repo = _make_service()
    created = await service.create(BookCreate(title="Test", author="Author"))
    repo.set_copies(created.id, 5)
    found = await service.get_by_id(created.id)
    assert found is not None
    assert found.copies_total == 5


async def test_get_filtered_empty() -> None:
    service, _ = _make_service()
    result = await service.get_filtered(None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.items == []
    assert result.total == 0
    assert result.pages == 0


async def test_get_filtered_with_books() -> None:
    service, _ = _make_service()
    await service.create(BookCreate(title="A", author="X"))
    await service.create(BookCreate(title="B", author="Y"))
    result = await service.get_filtered(None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert len(result.items) == 2
    assert result.total == 2
    assert result.pages == 1
    assert all(item.copies_total == 0 for item in result.items)


async def test_get_filtered_pagination() -> None:
    service, _ = _make_service()
    for i in range(5):
        await service.create(BookCreate(title=f"Book {i}", author="Author"))
    result = await service.get_filtered(None, None, SortBy.created_at, SortOrder.desc, 1, 3)
    assert len(result.items) == 3
    assert result.total == 5
    assert result.pages == 2


async def test_update_existing() -> None:
    service, _ = _make_service()
    created = await service.create(BookCreate(title="Old", author="Author"))
    updated = await service.update(created.id, BookUpdate(title="New"))
    assert updated is not None
    assert updated.title == "New"
    assert updated.author == "Author"


async def test_update_missing() -> None:
    service, _ = _make_service()
    result = await service.update(uuid.uuid4(), BookUpdate(title="X"))
    assert result is None


async def test_delete_existing() -> None:
    service, _ = _make_service()
    created = await service.create(BookCreate(title="Test", author="Author"))
    assert await service.delete(created.id) is True
    assert await service.get_by_id(created.id) is None


async def test_delete_missing() -> None:
    service, _ = _make_service()
    assert await service.delete(uuid.uuid4()) is False
