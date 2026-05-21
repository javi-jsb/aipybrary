from pathlib import Path

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


def test_env_py_imports_all_table_models() -> None:
    """Every domain model file that defines a table must be imported in env.py."""
    env_py = Path("alembic/env.py").read_text()
    missing = []
    for model_file in sorted(Path("src/app").rglob("*_model.py")):
        if "table=True" not in model_file.read_text():
            continue
        module = model_file.with_suffix("").as_posix().replace("src/", "").replace("/", ".")
        if f"import {module}" not in env_py:
            missing.append(f"import {module}  # noqa: F401")
    assert not missing, "alembic/env.py is missing:\n" + "\n".join(missing)
