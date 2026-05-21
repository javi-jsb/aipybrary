import re
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import field_validator
from sqlalchemy import String, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.core.entity import Entity
from app.core.pagination import PaginatedResponse
from app.core.sorting import SortOrder  # noqa: F401


class MemberStatus(StrEnum):
    active = "active"
    suspended = "suspended"


class SortBy(StrEnum):
    full_name = "full_name"
    email = "email"
    status = "status"
    created_at = "created_at"


# Name the email unique constraint explicitly so the SQL repository can tell an
# email collision apart from any other IntegrityError (see sql_member_repository).
EMAIL_CONSTRAINT = "uq_members_email"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(v: str | None) -> str | None:
    if v is None:
        return None
    normalized = v.strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise ValueError("Invalid email format")
    return normalized


class Member(Entity, table=True):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("email", name=EMAIL_CONSTRAINT),)

    full_name: str = Field(max_length=300)
    email: str = Field(max_length=320)
    status: MemberStatus = Field(default=MemberStatus.active, sa_type=String(length=20))


class MemberCreate(SQLModel):
    full_name: str = Field(max_length=300)
    email: str = Field(max_length=320)
    status: MemberStatus = MemberStatus.active

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        return _validate_email(v)


class MemberUpdate(SQLModel):
    full_name: str | None = Field(default=None, max_length=300)
    email: str | None = Field(default=None, max_length=320)
    status: MemberStatus | None = None

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        return _validate_email(v)


class MemberPublic(SQLModel):
    id: uuid.UUID
    full_name: str
    email: str
    status: MemberStatus
    created_at: datetime
    updated_at: datetime


class MemberListResponse(PaginatedResponse[MemberPublic]):
    pass
