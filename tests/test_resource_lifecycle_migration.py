"""Regression coverage for partially materialized resource lifecycle schema."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def _load_migration():
    path = Path(__file__).parents[1] / "migrations" / "versions" / "20260828_0025_resource_lifecycle.py"
    spec = importlib.util.spec_from_file_location("resource_lifecycle_0025", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_upgrade_tolerates_removed_at_already_existing():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    sa.Table("user", metadata, sa.Column("id", sa.Integer(), primary_key=True))
    sa.Table(
        "resource",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("removed_at", sa.DateTime(), nullable=True),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        migration = _load_migration()
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        inspector = sa.inspect(connection)
        columns = {column["name"] for column in inspector.get_columns("resource")}
        assert {"removed_at", "removed_by_id", "removal_reason"}.issubset(columns)
        assert any(
            foreign_key.get("constrained_columns") == ["removed_by_id"]
            and foreign_key.get("referred_table") == "user"
            for foreign_key in inspector.get_foreign_keys("resource")
        )
