import sqlalchemy as sa
from alembic.config import Config

from alembic import command
from app.config import settings
from tests.conftest import test_engine


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.test_database_url)
    return cfg


def _isbn_constraint_names(sync_conn: sa.Connection) -> set[str | None]:
    insp = sa.inspect(sync_conn)
    return {
        u["name"]
        for u in insp.get_unique_constraints("books")
        if tuple(u["column_names"]) == ("isbn",)
    }


async def test_books_isbn_constraint_is_named() -> None:
    async with test_engine.connect() as conn:
        names = await conn.run_sync(_isbn_constraint_names)
    assert "uq_books_isbn" in names


def test_books_isbn_constraint_rename_is_reversible() -> None:
    # This test is sync on purpose: alembic's env runs migrations on its own
    # event loop, which clashes with an async test's running loop. The autouse
    # db_setup fixture leaves the DB at head; pin revisions explicitly so a
    # relative "-1" / "head" never silently targets the wrong migration.
    cfg = _alembic_config()
    engine = sa.create_engine(settings.test_database_url)
    try:
        command.downgrade(cfg, "7f3a1c9d2b4e")  # the rename's down_revision
        with engine.connect() as conn:
            assert _isbn_constraint_names(conn) == {"books_isbn_key"}

        command.upgrade(cfg, "9c2e7b4f1a3d")  # the rename revision
        with engine.connect() as conn:
            assert _isbn_constraint_names(conn) == {"uq_books_isbn"}
    finally:
        engine.dispose()
