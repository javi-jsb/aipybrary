import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import computed_field
from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, SQLModel

from app.core.entity import Entity, _utcnow
from app.core.pagination import PaginatedResponse


class LoanStatus(StrEnum):
    active = "active"
    overdue = "overdue"
    returned = "returned"


class SortBy(StrEnum):
    created_at = "created_at"
    due_date = "due_date"
    returned_at = "returned_at"


# FK from loans to members (ON DELETE RESTRICT). Named so the member repository
# can recognise its violation and translate it into a domain-level error,
# mirroring BOOK_FK_CONSTRAINT for books.
MEMBER_FK_CONSTRAINT = "fk_loans_member_id_members"


class Loan(Entity, table=True):
    __tablename__ = "loans"

    member_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid(),
            ForeignKey("members.id", ondelete="RESTRICT", name=MEMBER_FK_CONSTRAINT),
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
