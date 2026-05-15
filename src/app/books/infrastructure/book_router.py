import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.books.application.book_service import BookService
from app.books.domain.book_model import BookCreate, BookPublic, BookUpdate
from app.books.infrastructure.sql_book_repository import SqlModelBookRepository
from app.database import get_session

router = APIRouter(prefix="/books", tags=["books"])


def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> BookService:
    return BookService(SqlModelBookRepository(session))


ServiceDep = Annotated[BookService, Depends(_get_service)]


@router.get("", response_model=list[BookPublic])
async def list_books(service: ServiceDep) -> list[BookPublic]:
    books = await service.get_all()
    return [BookPublic.model_validate(b) for b in books]


@router.get("/{book_id}", response_model=BookPublic)
async def get_book(book_id: uuid.UUID, service: ServiceDep) -> BookPublic:
    book = await service.get_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookPublic.model_validate(book)


@router.post("", response_model=BookPublic, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookCreate, service: ServiceDep) -> BookPublic:
    book = await service.create(data)
    return BookPublic.model_validate(book)


@router.patch("/{book_id}", response_model=BookPublic)
async def update_book(book_id: uuid.UUID, data: BookUpdate, service: ServiceDep) -> BookPublic:
    book = await service.update(book_id, data)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookPublic.model_validate(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: uuid.UUID, service: ServiceDep) -> None:
    deleted = await service.delete(book_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
