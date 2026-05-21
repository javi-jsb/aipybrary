import uuid

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

    def add(self, book: Book) -> None:
        self._books[book.id] = book

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
