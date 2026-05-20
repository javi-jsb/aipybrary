"""create book_copies table

Revision ID: 3e8f1d5c7a2b
Revises: 9c2e7b4f1a3d
Create Date: 2026-05-20 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision: str = "3e8f1d5c7a2b"
down_revision: str | Sequence[str] | None = "9c2e7b4f1a3d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "book_copies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("barcode", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("location", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["book_id"],
            ["books.id"],
            name="fk_book_copies_book_id_books",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("barcode", name="uq_book_copies_barcode"),
    )
    op.create_index("ix_book_copies_book_id", "book_copies", ["book_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_book_copies_book_id", table_name="book_copies")
    op.drop_table("book_copies")
