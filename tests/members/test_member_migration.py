import sqlalchemy as sa
from alembic.config import Config

from alembic import command
from app.config import settings
from tests.conftest import test_engine


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.test_database_url)
    return cfg


async def test_members_table_has_user_id_fk_and_no_email() -> None:
    async with test_engine.connect() as conn:

        def _inspect(sync_conn: sa.Connection) -> None:
            insp = sa.inspect(sync_conn)
            assert "members" in insp.get_table_names()
            columns = {c["name"] for c in insp.get_columns("members")}
            assert {"id", "full_name", "user_id", "status", "created_at", "updated_at"} <= columns
            assert "email" not in columns

            fks = insp.get_foreign_keys("members")
            fk_cols = {tuple(fk["constrained_columns"]) for fk in fks}
            assert ("user_id",) in fk_cols

            uniques = insp.get_unique_constraints("members")
            assert any(u["column_names"] == ["user_id"] for u in uniques)

        await conn.run_sync(_inspect)


def test_members_migration_is_reversible() -> None:
    cfg = _alembic_config()
    # Downgrade past the authentication revision that modified members.
    command.downgrade(cfg, "a1b2c3d4e5f6")  # authentication's down_revision (loans)
    # Re-apply the authentication migration.
    command.upgrade(cfg, "6c92b2f9eaef")
