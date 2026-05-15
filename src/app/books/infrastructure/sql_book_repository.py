import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.books.domain.book_model import Book, BookCreate, BookUpdate
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

    async def get_all(self) -> list[Book]:
        result = await self._session.exec(select(Book))
        return list(result.all())

    async def update(self, book: Book, data: BookUpdate) -> Book:
        book.sqlmodel_update(data.model_dump(exclude_unset=True))
        self._session.add(book)
        await self._session.commit()
        await self._session.refresh(book)
        return book

    async def delete(self, book: Book) -> None:
        await self._session.delete(book)
        await self._session.commit()
