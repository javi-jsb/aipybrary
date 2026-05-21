import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.books.application.book_service import BookService
from app.books.domain.book_exceptions import BookHasCopiesError, DuplicateIsbnError
from app.books.domain.book_model import (
    BookCreate,
    BookListResponse,
    BookPublic,
    BookUpdate,
    SortBy,
)
from app.books.infrastructure.sql_book_repository import SqlModelBookRepository
from app.core.sorting import SortOrder
from app.database import get_session

router = APIRouter(prefix="/books", tags=["books"])

_DUPLICATE_ISBN_DETAIL = "ISBN already registered"
_HAS_COPIES_DETAIL = "Book has copies and cannot be deleted"


def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> BookService:
    return BookService(SqlModelBookRepository(session))


ServiceDep = Annotated[BookService, Depends(_get_service)]


@router.get("", response_model=BookListResponse)
async def list_books(
    service: ServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    title: str | None = None,
    author: str | None = None,
    sort_by: SortBy = SortBy.created_at,
    order: SortOrder = SortOrder.desc,
) -> BookListResponse:
    return await service.get_filtered(title, author, sort_by, order, page, size)


@router.get("/{book_id}", response_model=BookPublic)
async def get_book(book_id: uuid.UUID, service: ServiceDep) -> BookPublic:
    book = await service.get_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.post("", response_model=BookPublic, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookCreate, service: ServiceDep) -> BookPublic:
    try:
        return await service.create(data)
    except DuplicateIsbnError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_ISBN_DETAIL) from None


@router.patch("/{book_id}", response_model=BookPublic)
async def update_book(book_id: uuid.UUID, data: BookUpdate, service: ServiceDep) -> BookPublic:
    try:
        book = await service.update(book_id, data)
    except DuplicateIsbnError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_ISBN_DETAIL) from None
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: uuid.UUID, service: ServiceDep) -> None:
    try:
        deleted = await service.delete(book_id)
    except BookHasCopiesError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_HAS_COPIES_DETAIL) from None
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
