import uuid
from datetime import UTC, datetime
from enum import StrEnum
from math import ceil

import uuid_utils
from pydantic import computed_field
from sqlalchemy import Column, ForeignKey, Uuid, text
from sqlmodel import Field, SQLModel


def _uuid7() -> uuid.UUID:
    return uuid.UUID(bytes=uuid_utils.uuid7().bytes)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class LoanStatus(StrEnum):
    active = "active"
    overdue = "overdue"
    returned = "returned"


class SortBy(StrEnum):
    created_at = "created_at"
    due_date = "due_date"
    returned_at = "returned_at"


class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"


class Loan(SQLModel, table=True):
    __tablename__ = "loans"

    id: uuid.UUID = Field(default_factory=_uuid7, primary_key=True)
    member_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid(),
            ForeignKey("members.id", ondelete="RESTRICT", name="fk_loans_member_id_members"),
            nullable=False,
            index=True,
        )
    )
    book_copy_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid(),
            ForeignKey("book_copies.id", ondelete="RESTRICT", name="fk_loans_book_copy_id_book_copies"),
            nullable=False,
            index=True,
        )
    )
    due_date: datetime
    returned_at: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()"), "onupdate": _utcnow},
    )


class LoanCreate(SQLModel):
    member_id: uuid.UUID
    book_copy_id: uuid.UUID


class LoanPublic(SQLModel):
    id: uuid.UUID
    member_id: uuid.UUID
    book_copy_id: uuid.UUID
    due_date: datetime
    returned_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def status(self) -> LoanStatus:
        if self.returned_at is not None:
            return LoanStatus.returned
        if self.due_date < _utcnow():
            return LoanStatus.overdue
        return LoanStatus.active


class LoanListResponse(SQLModel):
    items: list[LoanPublic]
    total: int
    page: int
    size: int

    @computed_field
    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.total > 0 else 0
