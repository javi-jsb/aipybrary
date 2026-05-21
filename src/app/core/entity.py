import uuid
from datetime import UTC, datetime

import uuid_utils
from sqlalchemy import text
from sqlmodel import Field, SQLModel


def _uuid7() -> uuid.UUID:
    return uuid.UUID(bytes=uuid_utils.uuid7().bytes)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Entity(SQLModel):
    id: uuid.UUID = Field(default_factory=_uuid7, primary_key=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()"), "onupdate": _utcnow},
    )
