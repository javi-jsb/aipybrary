import uuid

from app.books.domain.book_model import (
    Book,
    BookCreate,
    BookListResponse,
    BookPublic,
    BookUpdate,
    SortBy,
    SortOrder,
)
from app.books.domain.book_repository import BookRepository


class BookService:
    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    async def create(self, data: BookCreate) -> Book:
        return await self._repository.create(data)

    async def get_by_id(self, book_id: uuid.UUID) -> Book | None:
        return await self._repository.get_by_id(book_id)

    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> BookListResponse:
        books, total = await self._repository.get_filtered(
            title, author, sort_by, order, page, size
        )
        items = [BookPublic.model_validate(b) for b in books]
        return BookListResponse(items=items, total=total, page=page, size=size)

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
