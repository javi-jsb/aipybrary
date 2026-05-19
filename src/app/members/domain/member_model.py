import uuid
from datetime import UTC, datetime
from enum import StrEnum
from math import ceil

import uuid_utils
from pydantic import computed_field
from sqlalchemy import String, text
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
    created_at = "created_at"


class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"


class Member(SQLModel, table=True):
    __tablename__ = "members"

    id: uuid.UUID = Field(default_factory=_uuid7, primary_key=True)
    full_name: str = Field(max_length=300)
    email: str = Field(max_length=320, unique=True)
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


class MemberUpdate(SQLModel):
    full_name: str | None = Field(default=None, max_length=300)
    email: str | None = Field(default=None, max_length=320)
    status: MemberStatus | None = None


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
