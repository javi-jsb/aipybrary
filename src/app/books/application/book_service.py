import uuid

from app.books.domain.book_model import Book, BookCreate, BookUpdate
from app.books.domain.book_repository import BookRepository


class BookService:
    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    async def create(self, data: BookCreate) -> Book:
        return await self._repository.create(data)

    async def get_by_id(self, book_id: uuid.UUID) -> Book | None:
        return await self._repository.get_by_id(book_id)

    async def get_all(self) -> list[Book]:
        return await self._repository.get_all()

    async def update(self, book_id: uuid.UUID, data: BookUpdate) -> Book | None:
        book = await self._repository.get_by_id(book_id)
        if book is None:
            return None
        return await self._repository.update(book, data)

    async def delete(self, book_id: uuid.UUID) -> bool:
        book = await self._repository.get_by_id(book_id)
        if book is None:
            return False
        await self._repository.delete(book)
        return True
