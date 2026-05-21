import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import computed_field
from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, SQLModel

from app.core.entity import Entity, _utcnow
from app.core.pagination import PaginatedResponse
from app.core.sorting import SortOrder  # noqa: F401


class LoanStatus(StrEnum):
    active = "active"
    overdue = "overdue"
    returned = "returned"


class SortBy(StrEnum):
    created_at = "created_at"
    due_date = "due_date"
    returned_at = "returned_at"


class Loan(Entity, table=True):
    __tablename__ = "loans"

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


class LoanListResponse(PaginatedResponse[LoanPublic]):
    pass
