import uuid
from abc import ABC, abstractmethod
from typing import NamedTuple

from app.books.domain.book_model import Book, BookCreate, BookUpdate, SortBy, SortOrder


class BookWithCounts(NamedTuple):
    book: Book
    copies_total: int
    copies_available: int


class BookRepository(ABC):
    @abstractmethod
    async def create(self, data: BookCreate) -> Book: ...

    @abstractmethod
    async def get_by_id(self, book_id: uuid.UUID) -> BookWithCounts | None: ...

    @abstractmethod
    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[BookWithCounts], int]: ...

    @abstractmethod
    async def update(self, book: Book, data: BookUpdate) -> BookWithCounts: ...

    @abstractmethod
    async def delete(self, book: Book) -> None: ...
