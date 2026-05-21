import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlmodel import SQLModel

from app.config import settings


def test_no_schema_drift() -> None:
    """Autogenerate must produce no changes against a fully migrated DB."""
    engine = sa.create_engine(settings.test_database_url)
    try:
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            diff = compare_metadata(ctx, SQLModel.metadata)
        assert diff == [], f"Schema drift detected: {diff}"
    finally:
        engine.dispose()
