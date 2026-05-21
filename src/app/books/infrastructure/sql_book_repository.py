import uuid

from sqlalchemy import func, literal
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
from app.books.domain.book_repository import BookRepository, BookWithCounts
from app.core.db import is_constraint_violated
from app.loans.domain.loan_model import Loan

_copies_total_sq = (
    select(func.count(col(BookCopy.id))).where(col(BookCopy.book_id) == col(Book.id)).correlate(Book).scalar_subquery()
)

_active_loan_for_copy = (
    select(literal(1)).where(col(Loan.book_copy_id) == col(BookCopy.id)).where(col(Loan.returned_at).is_(None))
)

_copies_available_sq = (
    select(func.count(col(BookCopy.id)))
    .where(col(BookCopy.book_id) == col(Book.id))
    .where(~_active_loan_for_copy.exists())
    .correlate(Book)
    .scalar_subquery()
)


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
            if is_constraint_violated(exc, ISBN_CONSTRAINT):
                raise DuplicateIsbnError from exc
            raise
        await self._session.refresh(book)
        return book

    async def get_by_id(self, book_id: uuid.UUID) -> BookWithCounts | None:
        stmt = select(Book, _copies_total_sq, _copies_available_sq).where(col(Book.id) == book_id)
        row = (await self._session.exec(stmt)).first()
        if row is None:
            return None
        book, copies_total, copies_available = row
        return BookWithCounts(book, copies_total, copies_available)

    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[BookWithCounts], int]:
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

        stmt = select(Book, _copies_total_sq, _copies_available_sq)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ordered).offset((page - 1) * size).limit(size)
        result = await self._session.exec(stmt)
        return [BookWithCounts(book, ct, ca) for book, ct, ca in result.all()], total

    async def update(self, book: Book, data: BookUpdate) -> BookWithCounts:
        book.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._session.add(book)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if is_constraint_violated(exc, ISBN_CONSTRAINT):
                raise DuplicateIsbnError from exc
            raise
        await self._session.refresh(book)
        stmt = select(Book, _copies_total_sq, _copies_available_sq).where(col(Book.id) == book.id)
        row = (await self._session.exec(stmt)).one()
        _, copies_total, copies_available = row
        return BookWithCounts(book, copies_total, copies_available)

    async def delete(self, book: Book) -> None:
        await self._session.delete(book)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if is_constraint_violated(exc, BOOK_FK_CONSTRAINT):
                raise BookHasCopiesError from exc
            raise
