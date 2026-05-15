import uuid
from datetime import UTC, datetime

import uuid_utils
from sqlalchemy import text
from sqlmodel import Field, SQLModel


def _uuid7() -> uuid.UUID:
    return uuid.UUID(bytes=uuid_utils.uuid7().bytes)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: uuid.UUID = Field(default_factory=_uuid7, primary_key=True)
    title: str = Field(max_length=500)
    author: str = Field(max_length=300)
    isbn: str | None = Field(default=None, max_length=13, unique=True)
    publication_year: int | None = None
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()"), "onupdate": _utcnow},
    )


class BookCreate(SQLModel):
    title: str = Field(max_length=500)
    author: str = Field(max_length=300)
    isbn: str | None = Field(default=None, max_length=13)
    publication_year: int | None = None


class BookUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=500)
    author: str | None = Field(default=None, max_length=300)
    isbn: str | None = Field(default=None, max_length=13)
    publication_year: int | None = None


class BookPublic(SQLModel):
    id: uuid.UUID
    title: str
    author: str
    isbn: str | None
    publication_year: int | None
    created_at: datetime
    updated_at: datetime
