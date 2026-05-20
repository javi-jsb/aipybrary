import uuid
from abc import ABC, abstractmethod

from app.book_copies.domain.book_copy_model import (
    BookCopy,
    BookCopyCreate,
    BookCopyUpdate,
    SortBy,
    SortOrder,
)


class BookCopyRepository(ABC):
    @abstractmethod
    async def create(self, data: BookCopyCreate) -> BookCopy: ...

    @abstractmethod
    async def get_by_id(self, copy_id: uuid.UUID) -> BookCopy | None: ...

    @abstractmethod
    async def get_filtered(
        self,
        book_id: uuid.UUID | None,
        barcode: str | None,
        location: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[BookCopy], int]: ...

    @abstractmethod
    async def update(self, copy: BookCopy, data: BookCopyUpdate) -> BookCopy: ...

    @abstractmethod
    async def delete(self, copy: BookCopy) -> None: ...

    @abstractmethod
    async def count_by_book_id(self, book_id: uuid.UUID) -> int: ...
