import sqlalchemy as sa
from alembic.config import Config

from alembic import command
from app.config import settings
from tests.conftest import test_engine


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.test_database_url)
    return cfg


async def test_members_table_created_with_unique_email() -> None:
    async with test_engine.connect() as conn:

        def _inspect(sync_conn: sa.Connection) -> None:
            insp = sa.inspect(sync_conn)
            assert "members" in insp.get_table_names()
            columns = {c["name"] for c in insp.get_columns("members")}
            assert {"id", "full_name", "email", "status", "created_at", "updated_at"} <= columns
            unique_cols = {tuple(u["column_names"]) for u in insp.get_unique_constraints("members")}
            assert ("email",) in unique_cols

        await conn.run_sync(_inspect)


def test_members_migration_is_reversible() -> None:
    cfg = _alembic_config()
    # The autouse db_setup fixture leaves the DB at head; exercise the members
    # revision's downgrade then upgrade explicitly.
    command.downgrade(cfg, "-1")
    command.upgrade(cfg, "head")
