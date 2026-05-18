import uuid

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.books.domain.book_model import Book, BookCreate, BookUpdate, SortBy, SortOrder
from app.books.domain.book_repository import BookRepository


class SqlModelBookRepository(BookRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: BookCreate) -> Book:
        book = Book.model_validate(data)
        self._session.add(book)
        await self._session.commit()
        await self._session.refresh(book)
        return book

    async def get_by_id(self, book_id: uuid.UUID) -> Book | None:
        return await self._session.get(Book, book_id)

    async def get_filtered(
        self,
        title: str | None,
        author: str | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[Book], int]:
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

        stmt = select(Book)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ordered).offset((page - 1) * size).limit(size)
        result = await self._session.exec(stmt)
        return list(result.all()), total

    async def update(self, book: Book, data: BookUpdate) -> Book:
        book.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._session.add(book)
        await self._session.commit()
        await self._session.refresh(book)
        return book

    async def delete(self, book: Book) -> None:
        await self._session.delete(book)
        await self._session.commit()
