import uuid
from abc import ABC, abstractmethod

from app.books.domain.book_model import Book, BookCreate, BookUpdate


class BookRepository(ABC):
    @abstractmethod
    async def create(self, data: BookCreate) -> Book: ...

    @abstractmethod
    async def get_by_id(self, book_id: uuid.UUID) -> Book | None: ...

    @abstractmethod
    async def get_all(self) -> list[Book]: ...

    @abstractmethod
    async def update(self, book: Book, data: BookUpdate) -> Book: ...

    @abstractmethod
    async def delete(self, book: Book) -> None: ...
