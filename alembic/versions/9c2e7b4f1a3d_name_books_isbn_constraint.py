"""name books isbn unique constraint

Revision ID: 9c2e7b4f1a3d
Revises: 7f3a1c9d2b4e
Create Date: 2026-05-19 11:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "9c2e7b4f1a3d"
down_revision: str | Sequence[str] | None = "7f3a1c9d2b4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The original create-books migration emitted an *unnamed* UNIQUE(isbn). Postgres
# then assigns its deterministic default name `<table>_<column>_key`, i.e.
# `books_isbn_key`. We rename it to the explicit `uq_books_isbn` so the SQL
# repository can match the constraint by name (mirroring `uq_members_email`) and
# distinguish an ISBN collision from any other integrity violation.
_OLD_NAME = "books_isbn_key"
_NEW_NAME = "uq_books_isbn"


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(_OLD_NAME, "books", type_="unique")
    op.create_unique_constraint(_NEW_NAME, "books", ["isbn"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_NEW_NAME, "books", type_="unique")
    op.create_unique_constraint(_OLD_NAME, "books", ["isbn"])
