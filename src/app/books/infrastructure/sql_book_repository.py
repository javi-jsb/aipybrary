import uuid

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.book_copies.domain.book_copy_model import BOOK_FK_CONSTRAINT, BookCopy
from app.books.domain.book_exceptions import BookHasCopiesError, DuplicateIsbnError
from app.books.domain.book_model import (
    ISBN_CONSTRAINT,
    Book,
    BookCreate,
    BookUpdate,
    SortBy,
    SortOrder,
)
from app.books.domain.book_repository import BookRepository


def _is_isbn_conflict(exc: IntegrityError) -> bool:
    """True only when the violated constraint is the isbn unique index.

    Any other IntegrityError (e.g. a NOT NULL violation) is left to propagate
    untouched rather than being mislabelled as a duplicate-isbn 409.
    """
    return exc.orig is not None and ISBN_CONSTRAINT in str(exc.orig)


def _is_book_copies_fk_conflict(exc: IntegrityError) -> bool:
    """True only when the violated constraint is the book_copies → books FK.

    Any other IntegrityError is left to propagate untouched rather than being
    mislabelled as a copies-blocking-delete 409.
    """
    return exc.orig is not None and BOOK_FK_CONSTRAINT in str(exc.orig)


class SqlModelBookRepository(BookRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: BookCreate) -> Book:
        book = Book.model_validate(data)
        self._session.add(book)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if _is_isbn_conflict(exc):
                raise DuplicateIsbnError from exc
            raise
        await self._session.refresh(book)
        return book

    async def get_by_id(self, book_id: uuid.UUID) -> tuple[Book, int] | None:
        stmt = (
            select(Book, func.count(col(BookCopy.id)))
            .outerjoin(BookCopy, col(BookCopy.book_id) == col(Book.id))
            .where(col(Book.id) == book_id)
            .group_by(col(Book.id))
        )
        row = (await self._session.exec(stmt)).first()
        if row is None:
            return None
        book, copies_total = row
        return book, copies_total

    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[tuple[Book, int]], int]:
        conditions = []
        if title:
            conditions.append(col(Book.title).ilike(f"%{title}%"))
        if author:
            conditions.append(col(Book.author).ilike(f"%{author}%"))

        sort_attr = getattr(Book, sort_by.value)
        ordered = sort_attr.desc() if order == SortOrder.desc else sort_attr.asc()

        count_stmt = select(func.count(col(Book.id)))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total: int = (await self._session.exec(count_stmt)).one()

        stmt = (
            select(Book, func.count(col(BookCopy.id)))
            .outerjoin(BookCopy, col(BookCopy.book_id) == col(Book.id))
            .group_by(col(Book.id))
        )
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ordered).offset((page - 1) * size).limit(size)
        result = await self._session.exec(stmt)
        return [(book, copies) for book, copies in result.all()], total

    async def update(self, book: Book, data: BookUpdate) -> tuple[Book, int]:
        book.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._session.add(book)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if _is_isbn_conflict(exc):
                raise DuplicateIsbnError from exc
            raise
        await self._session.refresh(book)
        count_stmt = select(func.count(col(BookCopy.id))).where(col(BookCopy.book_id) == book.id)
        copies_total: int = (await self._session.exec(count_stmt)).one()
        return book, copies_total

    async def delete(self, book: Book) -> None:
        await self._session.delete(book)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if _is_book_copies_fk_conflict(exc):
                raise BookHasCopiesError from exc
            raise
