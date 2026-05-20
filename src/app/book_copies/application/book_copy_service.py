import uuid

from app.book_copies.domain.book_copy_exceptions import BookCopyBookNotFoundError
from app.book_copies.domain.book_copy_model import (
    BookCopy,
    BookCopyCreate,
    BookCopyListResponse,
    BookCopyPublic,
    BookCopyUpdate,
    SortBy,
    SortOrder,
)
from app.book_copies.domain.book_copy_repository import BookCopyRepository
from app.books.domain.book_repository import BookRepository


class BookCopyService:
    def __init__(
        self,
        book_copy_repository: BookCopyRepository,
        book_repository: BookRepository,
    ) -> None:
        self._book_copy_repository = book_copy_repository
        self._book_repository = book_repository

    async def create(self, data: BookCopyCreate) -> BookCopy:
        book = await self._book_repository.get_by_id(data.book_id)
        if book is None:
            raise BookCopyBookNotFoundError
        return await self._book_copy_repository.create(data)

    async def get_by_id(self, copy_id: uuid.UUID) -> BookCopy | None:
        return await self._book_copy_repository.get_by_id(copy_id)

    async def get_filtered(
        self,
        book_id: uuid.UUID | None,
        barcode: str | None,
        location: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> BookCopyListResponse:
        copies, total = await self._book_copy_repository.get_filtered(
            book_id, barcode, location, sort_by, order, page, size
        )
        items = [BookCopyPublic.model_validate(c) for c in copies]
        return BookCopyListResponse(items=items, total=total, page=page, size=size)

    async def update(self, copy_id: uuid.UUID, data: BookCopyUpdate) -> BookCopy | None:
        copy = await self._book_copy_repository.get_by_id(copy_id)
        if copy is None:
            return None
        return await self._book_copy_repository.update(copy, data)

    async def delete(self, copy_id: uuid.UUID) -> bool:
        copy = await self._book_copy_repository.get_by_id(copy_id)
        if copy is None:
            return False
        await self._book_copy_repository.delete(copy)
        return True
