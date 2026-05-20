import uuid
from datetime import UTC, datetime
from enum import StrEnum
from math import ceil

import uuid_utils
from pydantic import computed_field
from sqlalchemy import Text, UniqueConstraint, text
from sqlmodel import Field, SQLModel


def _uuid7() -> uuid.UUID:
    return uuid.UUID(bytes=uuid_utils.uuid7().bytes)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class SortBy(StrEnum):
    barcode = "barcode"
    location = "location"
    created_at = "created_at"


class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"


# Named constraints so the SQL repository can distinguish a barcode collision or
# a book FK violation from any other IntegrityError (see sql_book_copy_repository
# and sql_book_repository).
BARCODE_CONSTRAINT = "uq_book_copies_barcode"
BOOK_FK_CONSTRAINT = "fk_book_copies_book_id_books"


class BookCopy(SQLModel, table=True):
    __tablename__ = "book_copies"
    __table_args__ = (UniqueConstraint("barcode", name=BARCODE_CONSTRAINT),)

    id: uuid.UUID = Field(default_factory=_uuid7, primary_key=True)
    book_id: uuid.UUID = Field(foreign_key="books.id")
    barcode: str = Field(max_length=100)
    location: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, sa_type=Text())
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()"), "onupdate": _utcnow},
    )


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


class BookCopyListResponse(SQLModel):
    items: list[BookCopyPublic]
    total: int
    page: int
    size: int

    @computed_field
    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.total > 0 else 0
