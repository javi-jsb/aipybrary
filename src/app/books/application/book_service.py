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


def _to_public(book: Book, copies_total: int) -> BookPublic:
    return BookPublic.model_validate({**book.model_dump(), "copies_total": copies_total})


class BookService:
    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    async def create(self, data: BookCreate) -> BookPublic:
        # A freshly created book always has zero copies; skip the count query.
        book = await self._repository.create(data)
        return _to_public(book, 0)

    async def get_by_id(self, book_id: uuid.UUID) -> BookPublic | None:
        result = await self._repository.get_by_id(book_id)
        if result is None:
            return None
        book, copies_total = result
        return _to_public(book, copies_total)

    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> BookListResponse:
        rows, total = await self._repository.get_filtered(title, author, sort_by, order, page, size)
        items = [_to_public(book, copies) for book, copies in rows]
        return BookListResponse(items=items, total=total, page=page, size=size)

    async def update(self, book_id: uuid.UUID, data: BookUpdate) -> BookPublic | None:
        result = await self._repository.get_by_id(book_id)
        if result is None:
            return None
        book, _ = result
        updated, copies_total = await self._repository.update(book, data)
        return _to_public(updated, copies_total)

    async def delete(self, book_id: uuid.UUID) -> bool:
        result = await self._repository.get_by_id(book_id)
        if result is None:
            return False
        book, _ = result
        await self._repository.delete(book)
        return True
