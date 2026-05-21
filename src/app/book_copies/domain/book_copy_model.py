import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, ForeignKey, Text, UniqueConstraint, Uuid
from sqlmodel import Field, SQLModel

from app.core.entity import Entity
from app.core.pagination import PaginatedResponse


class SortBy(StrEnum):
    barcode = "barcode"
    location = "location"
    created_at = "created_at"


# Named constraints so the SQL repository can distinguish a barcode collision or
# a book FK violation from any other IntegrityError (see sql_book_copy_repository
# and sql_book_repository).
BARCODE_CONSTRAINT = "uq_book_copies_barcode"
BOOK_FK_CONSTRAINT = "fk_book_copies_book_id_books"


class BookCopy(Entity, table=True):
    __tablename__ = "book_copies"
    __table_args__ = (UniqueConstraint("barcode", name=BARCODE_CONSTRAINT),)

    book_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid(),
            ForeignKey("books.id", ondelete="RESTRICT", name=BOOK_FK_CONSTRAINT),
            nullable=False,
            index=True,
        )
    )
    barcode: str = Field(max_length=100)
    location: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, sa_type=Text())


class BookCopyCreate(SQLModel):
    book_id: uuid.UUID
    barcode: str = Field(max_length=100)
    location: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class BookCopyUpdate(SQLModel):
    model_config = {"extra": "forbid"}  # reject `book_id` (a copy is not reassignable)

    barcode: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class BookCopyPublic(SQLModel):
    id: uuid.UUID
    book_id: uuid.UUID
    barcode: str
    location: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class BookCopyListResponse(PaginatedResponse[BookCopyPublic]):
    pass
