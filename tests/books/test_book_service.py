import uuid

from app.books.application.book_service import BookService
from app.books.domain.book_model import Book, BookCreate, BookUpdate, SortBy, SortOrder
from app.books.domain.book_repository import BookRepository, BookWithCounts


class FakeBookRepository(BookRepository):
    """In-memory repository that simulates the (Book, copies_total, copies_available) tuples
    the SQL repository returns. Copy counts are populated by tests via
    ``set_copies(book_id, n)``.
    """

    def __init__(self) -> None:
        self._books: dict[uuid.UUID, Book] = {}
        self._copies: dict[uuid.UUID, int] = {}

    def set_copies(self, book_id: uuid.UUID, n: int) -> None:
        self._copies[book_id] = n

    def _count(self, book_id: uuid.UUID) -> int:
        return self._copies.get(book_id, 0)

    async def create(self, data: BookCreate) -> Book:
        book = Book.model_validate(data)
        self._books[book.id] = book
        return book

    async def get_by_id(self, book_id: uuid.UUID) -> BookWithCounts | None:
        book = self._books.get(book_id)
        if book is None:
            return None
        n = self._count(book_id)
        return BookWithCounts(book, n, n)

    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[BookWithCounts], int]:
        books = list(self._books.values())
        if title:
            books = [b for b in books if title.lower() in b.title.lower()]
        if author:
            books = [b for b in books if author.lower() in b.author.lower()]
        total = len(books)
        offset = (page - 1) * size
        sliced = books[offset : offset + size]
        return [BookWithCounts(b, self._count(b.id), self._count(b.id)) for b in sliced], total

    async def update(self, book: Book, data: BookUpdate) -> BookWithCounts:
        book.sqlmodel_update(data.model_dump(exclude_unset=True))
        n = self._count(book.id)
        return BookWithCounts(book, n, n)

    async def delete(self, book: Book) -> None:
        self._books.pop(book.id, None)
        self._copies.pop(book.id, None)


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
