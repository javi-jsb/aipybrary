"""create loans table

Revision ID: a1b2c3d4e5f6
Revises: 3e8f1d5c7a2b
Create Date: 2026-05-21 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "3e8f1d5c7a2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "loans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("book_copy_id", sa.Uuid(), nullable=False),
        sa.Column("due_date", sa.DateTime(), nullable=False),
        sa.Column("returned_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
            name="fk_loans_member_id_members",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["book_copy_id"],
            ["book_copies.id"],
            name="fk_loans_book_copy_id_book_copies",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_loans_member_id", "loans", ["member_id"])
    op.create_index("ix_loans_book_copy_id", "loans", ["book_copy_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_loans_book_copy_id", table_name="loans")
    op.drop_index("ix_loans_member_id", table_name="loans")
    op.drop_table("loans")
