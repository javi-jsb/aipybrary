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
            uniques = insp.get_unique_constraints("members")
            assert ("email",) in {tuple(u["column_names"]) for u in uniques}
            assert any(u["name"] == "uq_members_email" for u in uniques)

        await conn.run_sync(_inspect)


def test_members_migration_is_reversible() -> None:
    cfg = _alembic_config()
    # The autouse db_setup fixture leaves the DB at head. Pin to the members
    # revision and its down_revision explicitly: a relative "-1" / "head" would
    # silently target the wrong migration once later revisions stack on top.
    command.downgrade(cfg, "ca883df3f8a5")  # members' down_revision
    command.upgrade(cfg, "7f3a1c9d2b4e")  # the members revision
