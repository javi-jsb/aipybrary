"""create members table

Revision ID: 7f3a1c9d2b4e
Revises: ca883df3f8a5
Create Date: 2026-05-19 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision: str = "7f3a1c9d2b4e"
down_revision: str | Sequence[str] | None = "ca883df3f8a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=320), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_members_email"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("members")
