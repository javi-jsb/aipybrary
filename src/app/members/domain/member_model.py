import re
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from math import ceil

import uuid_utils
from pydantic import computed_field, field_validator
from sqlalchemy import String, UniqueConstraint, text
from sqlmodel import Field, SQLModel


def _uuid7() -> uuid.UUID:
    return uuid.UUID(bytes=uuid_utils.uuid7().bytes)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class MemberStatus(StrEnum):
    active = "active"
    suspended = "suspended"


class SortBy(StrEnum):
    full_name = "full_name"
    email = "email"
    status = "status"
    created_at = "created_at"


class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"


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


class Member(SQLModel, table=True):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("email", name=EMAIL_CONSTRAINT),)

    id: uuid.UUID = Field(default_factory=_uuid7, primary_key=True)
    full_name: str = Field(max_length=300)
    email: str = Field(max_length=320)
    status: MemberStatus = Field(default=MemberStatus.active, sa_type=String(length=20))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()"), "onupdate": _utcnow},
    )


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


class MemberListResponse(SQLModel):
    items: list[MemberPublic]
    total: int
    page: int
    size: int

    @computed_field
    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.total > 0 else 0
