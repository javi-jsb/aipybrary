import uuid

from app.book_copies.domain.book_copy_model import (
    BookCopy,
    BookCopyCreate,
    BookCopyUpdate,
    SortBy,
    SortOrder,
)
from app.book_copies.domain.book_copy_repository import BookCopyRepository


class FakeBookCopyRepository(BookCopyRepository):
    def __init__(self) -> None:
        self._copies: dict[uuid.UUID, BookCopy] = {}

    def add(self, copy: BookCopy) -> None:
        self._copies[copy.id] = copy

    async def create(self, data: BookCopyCreate) -> BookCopy:
        copy = BookCopy.model_validate(data)
        self._copies[copy.id] = copy
        return copy

    async def get_by_id(self, copy_id: uuid.UUID) -> BookCopy | None:
        return self._copies.get(copy_id)

    async def get_filtered(
        self,
        book_id: uuid.UUID | None,
        barcode: str | None,
        location: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[BookCopy], int]:
        items = list(self._copies.values())
        if book_id is not None:
            items = [c for c in items if c.book_id == book_id]
        if barcode:
            items = [c for c in items if barcode.lower() in c.barcode.lower()]
        if location:
            items = [c for c in items if c.location and location.lower() in c.location.lower()]
        total = len(items)
        offset = (page - 1) * size
        return items[offset : offset + size], total

    async def update(self, copy: BookCopy, data: BookCopyUpdate) -> BookCopy:
        copy.sqlmodel_update(data.model_dump(exclude_unset=True))
        return copy

    async def delete(self, copy: BookCopy) -> None:
        self._copies.pop(copy.id, None)

    async def count_by_book_id(self, book_id: uuid.UUID) -> int:
        return sum(1 for c in self._copies.values() if c.book_id == book_id)
