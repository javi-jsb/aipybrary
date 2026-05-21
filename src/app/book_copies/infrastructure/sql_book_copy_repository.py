import uuid

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.book_copies.domain.book_copy_exceptions import DuplicateBarcodeError
from app.book_copies.domain.book_copy_model import (
    BARCODE_CONSTRAINT,
    BookCopy,
    BookCopyCreate,
    BookCopyUpdate,
    SortBy,
    SortOrder,
)
from app.book_copies.domain.book_copy_repository import BookCopyRepository
from app.core.db import is_constraint_violated


class SqlModelBookCopyRepository(BookCopyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: BookCopyCreate) -> BookCopy:
        copy = BookCopy.model_validate(data)
        self._session.add(copy)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if is_constraint_violated(exc, BARCODE_CONSTRAINT):
                raise DuplicateBarcodeError from exc
            raise
        await self._session.refresh(copy)
        return copy

    async def get_by_id(self, copy_id: uuid.UUID) -> BookCopy | None:
        return await self._session.get(BookCopy, copy_id)

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
        conditions = []
        if book_id is not None:
            conditions.append(col(BookCopy.book_id) == book_id)
        if barcode:
            conditions.append(col(BookCopy.barcode).ilike(f"%{barcode}%"))
        if location:
            conditions.append(col(BookCopy.location).ilike(f"%{location}%"))

        sort_attr = getattr(BookCopy, sort_by.value)
        ordered = sort_attr.desc() if order == SortOrder.desc else sort_attr.asc()

        count_stmt = select(func.count(col(BookCopy.id)))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total: int = (await self._session.exec(count_stmt)).one()

        stmt = select(BookCopy)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ordered).offset((page - 1) * size).limit(size)
        result = await self._session.exec(stmt)
        return list(result.all()), total

    async def update(self, copy: BookCopy, data: BookCopyUpdate) -> BookCopy:
        copy.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._session.add(copy)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if is_constraint_violated(exc, BARCODE_CONSTRAINT):
                raise DuplicateBarcodeError from exc
            raise
        await self._session.refresh(copy)
        return copy

    async def delete(self, copy: BookCopy) -> None:
        await self._session.delete(copy)
        await self._session.commit()

    async def count_by_book_id(self, book_id: uuid.UUID) -> int:
        stmt = select(func.count(col(BookCopy.id))).where(col(BookCopy.book_id) == book_id)
        return (await self._session.exec(stmt)).one()
