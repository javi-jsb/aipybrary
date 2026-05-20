import sqlalchemy as sa
from alembic.config import Config

from alembic import command
from app.config import settings
from tests.conftest import test_engine


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.test_database_url)
    return cfg


async def test_book_copies_table_created_with_constraints() -> None:
    async with test_engine.connect() as conn:

        def _inspect(sync_conn: sa.Connection) -> None:
            insp = sa.inspect(sync_conn)
            assert "book_copies" in insp.get_table_names()

            columns = {c["name"] for c in insp.get_columns("book_copies")}
            expected = {
                "id",
                "book_id",
                "barcode",
                "location",
                "notes",
                "created_at",
                "updated_at",
            }
            assert expected <= columns

            uniques = insp.get_unique_constraints("book_copies")
            assert ("barcode",) in {tuple(u["column_names"]) for u in uniques}
            assert any(u["name"] == "uq_book_copies_barcode" for u in uniques)

            fks = insp.get_foreign_keys("book_copies")
            book_fks = [
                fk
                for fk in fks
                if fk["referred_table"] == "books" and fk["constrained_columns"] == ["book_id"]
            ]
            assert book_fks, "expected FK from book_copies.book_id to books.id"
            fk = book_fks[0]
            assert fk["name"] == "fk_book_copies_book_id_books"
            assert (fk.get("options") or {}).get("ondelete") == "RESTRICT"

            indexes = insp.get_indexes("book_copies")
            assert any(ix["column_names"] == ["book_id"] for ix in indexes)

        await conn.run_sync(_inspect)


def test_book_copies_migration_is_reversible() -> None:
    cfg = _alembic_config()
    # The autouse db_setup fixture leaves the DB at head. Pin to the book_copies
    # revision and its down_revision explicitly: a relative "-1" / "head" would
    # silently target the wrong migration once later revisions stack on top.
    command.downgrade(cfg, "9c2e7b4f1a3d")  # book_copies' down_revision
    command.upgrade(cfg, "3e8f1d5c7a2b")  # the book_copies revision
