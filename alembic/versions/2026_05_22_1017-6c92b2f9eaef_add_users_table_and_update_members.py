"""add users table and update members

Revision ID: 6c92b2f9eaef
Revises: a1b2c3d4e5f6
Create Date: 2026-05-22 10:17:19.528323

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision: str = "6c92b2f9eaef"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=320), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    # `user_id` is added NOT NULL with no server default: this assumes `members`
    # is empty when the migration runs (clean rebuilds; no production data yet).
    # A populated table would need a 3-step nullable -> backfill -> SET NOT NULL.
    op.add_column("members", sa.Column("user_id", sa.Uuid(), nullable=False))
    op.drop_constraint("uq_members_email", "members", type_="unique")
    op.create_unique_constraint("uq_members_user_id", "members", ["user_id"])
    op.create_foreign_key("fk_members_user_id", "members", "users", ["user_id"], ["id"])
    op.drop_column("members", "email")


def downgrade() -> None:
    """Downgrade schema."""
    # Add email as nullable (any existing rows have no email to restore; this migration
    # is only exercised in test teardown where the table is subsequently dropped).
    op.add_column("members", sa.Column("email", sa.VARCHAR(length=320), nullable=True))
    op.create_unique_constraint("uq_members_email", "members", ["email"])
    op.drop_constraint("fk_members_user_id", "members", type_="foreignkey")
    op.drop_constraint("uq_members_user_id", "members", type_="unique")
    op.drop_column("members", "user_id")
    op.drop_table("users")
