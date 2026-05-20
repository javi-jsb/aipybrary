import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.book_copies.application.book_copy_service import BookCopyService
from app.book_copies.domain.book_copy_exceptions import (
    BookCopyBookNotFoundError,
    DuplicateBarcodeError,
)
from app.book_copies.domain.book_copy_model import (
    BookCopyCreate,
    BookCopyListResponse,
    BookCopyPublic,
    BookCopyUpdate,
    SortBy,
    SortOrder,
)
from app.book_copies.infrastructure.sql_book_copy_repository import SqlModelBookCopyRepository
from app.books.infrastructure.sql_book_repository import SqlModelBookRepository
from app.database import get_session

router = APIRouter(prefix="/book-copies", tags=["book-copies"])

_DUPLICATE_BARCODE_DETAIL = "Barcode already registered"
_BOOK_NOT_FOUND_DETAIL = "book_id does not reference an existing book"


def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> BookCopyService:
    return BookCopyService(SqlModelBookCopyRepository(session), SqlModelBookRepository(session))


ServiceDep = Annotated[BookCopyService, Depends(_get_service)]


@router.get("", response_model=BookCopyListResponse)
async def list_book_copies(
    service: ServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    book_id: uuid.UUID | None = None,
    barcode: str | None = None,
    location: str | None = None,
    sort_by: SortBy = SortBy.created_at,
    order: SortOrder = SortOrder.desc,
) -> BookCopyListResponse:
    return await service.get_filtered(book_id, barcode, location, sort_by, order, page, size)


@router.get("/{copy_id}", response_model=BookCopyPublic)
async def get_book_copy(copy_id: uuid.UUID, service: ServiceDep) -> BookCopyPublic:
    copy = await service.get_by_id(copy_id)
    if copy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book copy not found")
    return BookCopyPublic.model_validate(copy)


@router.post("", response_model=BookCopyPublic, status_code=status.HTTP_201_CREATED)
async def create_book_copy(data: BookCopyCreate, service: ServiceDep) -> BookCopyPublic:
    try:
        copy = await service.create(data)
    except BookCopyBookNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=_BOOK_NOT_FOUND_DETAIL
        ) from None
    except DuplicateBarcodeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_BARCODE_DETAIL
        ) from None
    return BookCopyPublic.model_validate(copy)


@router.patch("/{copy_id}", response_model=BookCopyPublic)
async def update_book_copy(
    copy_id: uuid.UUID, data: BookCopyUpdate, service: ServiceDep
) -> BookCopyPublic:
    try:
        copy = await service.update(copy_id, data)
    except DuplicateBarcodeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_BARCODE_DETAIL
        ) from None
    if copy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book copy not found")
    return BookCopyPublic.model_validate(copy)


@router.delete("/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_copy(copy_id: uuid.UUID, service: ServiceDep) -> None:
    deleted = await service.delete(copy_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book copy not found")
