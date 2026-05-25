import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.core.entity import Entity

EMAIL_CONSTRAINT = "uq_users_email"


class UserRole(StrEnum):
    admin = "admin"
    staff = "staff"
    member = "member"


class User(Entity, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name=EMAIL_CONSTRAINT),)

    email: str = Field(max_length=320)
    password_hash: str
    role: UserRole = Field(sa_type=String(length=20))
    is_active: bool = Field(default=True)


class UserPublic(SQLModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
