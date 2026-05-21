import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import field_validator
from sqlalchemy import Text, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.core.entity import Entity
from app.core.pagination import PaginatedResponse
from app.core.sorting import SortOrder  # noqa: F401


class SortBy(StrEnum):
    title = "title"
    author = "author"
    publication_year = "publication_year"
    created_at = "created_at"


def _validate_isbn(v: str | None) -> str | None:
    if v is None:
        return None
    stripped = v.replace("-", "")
    if len(stripped) == 10:
        if not stripped[:9].isdigit() or stripped[9] not in "0123456789X":
            raise ValueError("Invalid ISBN-10 format")
        total = sum(int(stripped[i]) * (10 - i) for i in range(9))
        check = 10 if stripped[9] == "X" else int(stripped[9])
        if (total + check) % 11 != 0:
            raise ValueError("Invalid ISBN-10 checksum")
    elif len(stripped) == 13:
        if not stripped.isdigit():
            raise ValueError("Invalid ISBN-13 format")
        total = sum(int(stripped[i]) * (1 if i % 2 == 0 else 3) for i in range(13))
        if total % 10 != 0:
            raise ValueError("Invalid ISBN-13 checksum")
    else:
        raise ValueError("ISBN must be 10 or 13 digits after stripping hyphens")
    return stripped


ISBN_CONSTRAINT = "uq_books_isbn"


class Book(Entity, table=True):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("isbn", name=ISBN_CONSTRAINT),)

    title: str = Field(max_length=500)
    author: str = Field(max_length=300)
    isbn: str | None = Field(default=None, max_length=13)
    publication_year: int | None = None
    synopsis: str | None = Field(default=None, sa_type=Text())


class BookCreate(SQLModel):
    title: str = Field(max_length=500)
    author: str = Field(max_length=300)
    isbn: str | None = None
    publication_year: int | None = None
    synopsis: str | None = None

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        return _validate_isbn(v)


class BookUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=500)
    author: str | None = Field(default=None, max_length=300)
    isbn: str | None = None
    publication_year: int | None = None
    synopsis: str | None = None

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        return _validate_isbn(v)


class BookPublic(SQLModel):
    id: uuid.UUID
    title: str
    author: str
    isbn: str | None
    publication_year: int | None
    synopsis: str | None
    copies_total: int
    copies_available: int
    created_at: datetime
    updated_at: datetime


class BookListResponse(PaginatedResponse[BookPublic]):
    pass
