import re
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import field_validator
from sqlalchemy import String
from sqlmodel import Field, SQLModel

from app.core.entity import Entity
from app.core.pagination import PaginatedResponse

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(v: str) -> str:
    normalized = v.strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise ValueError("Invalid email format")
    return normalized


class MemberStatus(StrEnum):
    active = "active"
    suspended = "suspended"


class SortBy(StrEnum):
    full_name = "full_name"
    email = "email"
    status = "status"
    created_at = "created_at"


class Member(Entity, table=True):
    __tablename__ = "members"

    full_name: str = Field(max_length=300)
    status: MemberStatus = Field(default=MemberStatus.active, sa_type=String(length=20))
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True)


class MemberCreate(SQLModel):
    full_name: str = Field(max_length=300)
    email: str = Field(max_length=320)
    status: MemberStatus = MemberStatus.active

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)


class MemberUpdate(SQLModel):
    full_name: str | None = Field(default=None, max_length=300)
    status: MemberStatus | None = None


class MemberPublic(SQLModel):
    id: uuid.UUID
    full_name: str
    email: str
    status: MemberStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_member(cls, member: Member, email: str) -> "MemberPublic":
        return cls(
            id=member.id,
            full_name=member.full_name,
            email=email,
            status=member.status,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )


class MemberCreateResponse(MemberPublic):
    initial_password: str


class MemberListResponse(PaginatedResponse[MemberPublic]):
    pass
