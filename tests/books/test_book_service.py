import uuid

from app.books.application.book_service import BookService
from app.books.domain.book_model import Book, BookCreate, BookUpdate
from app.books.domain.book_repository import BookRepository


class FakeBookRepository(BookRepository):
    def __init__(self) -> None:
        self._books: dict[uuid.UUID, Book] = {}

    async def create(self, data: BookCreate) -> Book:
        book = Book.model_validate(data)
        self._books[book.id] = book
        return book

    async def get_by_id(self, book_id: uuid.UUID) -> Book | None:
        return self._books.get(book_id)

    async def get_all(self) -> list[Book]:
        return list(self._books.values())

    async def update(self, book: Book, data: BookUpdate) -> Book:
        book.sqlmodel_update(data.model_dump(exclude_unset=True))
        return book

    async def delete(self, book: Book) -> None:
        self._books.pop(book.id, None)


def _make_service() -> BookService:
    return BookService(FakeBookRepository())


async def test_create_book() -> None:
    service = _make_service()
    book = await service.create(BookCreate(title="Test", author="Author"))
    assert book.title == "Test"
    assert book.author == "Author"
    assert book.id is not None


async def test_get_by_id_existing() -> None:
    service = _make_service()
    created = await service.create(BookCreate(title="Test", author="Author"))
    found = await service.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id


async def test_get_by_id_missing() -> None:
    service = _make_service()
    result = await service.get_by_id(uuid.uuid4())
    assert result is None


async def test_get_all_empty() -> None:
    service = _make_service()
    assert await service.get_all() == []


async def test_get_all_with_books() -> None:
    service = _make_service()
    await service.create(BookCreate(title="A", author="X"))
    await service.create(BookCreate(title="B", author="Y"))
    books = await service.get_all()
    assert len(books) == 2


async def test_update_existing() -> None:
    service = _make_service()
    created = await service.create(BookCreate(title="Old", author="Author"))
    updated = await service.update(created.id, BookUpdate(title="New"))
    assert updated is not None
    assert updated.title == "New"
    assert updated.author == "Author"


async def test_update_missing() -> None:
    service = _make_service()
    result = await service.update(uuid.uuid4(), BookUpdate(title="X"))
    assert result is None


async def test_delete_existing() -> None:
    service = _make_service()
    created = await service.create(BookCreate(title="Test", author="Author"))
    assert await service.delete(created.id) is True
    assert await service.get_by_id(created.id) is None


async def test_delete_missing() -> None:
    service = _make_service()
    assert await service.delete(uuid.uuid4()) is False
