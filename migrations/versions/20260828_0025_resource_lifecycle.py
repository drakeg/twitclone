"""add resource lifecycle audit metadata

Revision ID: 20260828_0025
Revises: 20260828_0024
"""

from alembic import op
import sqlalchemy as sa


revision = "20260828_0025"
down_revision = "20260828_0024"
branch_labels = None
depends_on = None


def _resource_columns():
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns("resource")}


def _has_removed_by_foreign_key():
    inspector = sa.inspect(op.get_bind())
    return any(
        foreign_key.get("constrained_columns") == ["removed_by_id"]
        and foreign_key.get("referred_table") == "user"
        for foreign_key in inspector.get_foreign_keys("resource")
    )


def upgrade():
    columns = _resource_columns()
    with op.batch_alter_table("resource") as batch_op:
        if "removed_at" not in columns:
            batch_op.add_column(sa.Column("removed_at", sa.DateTime(), nullable=True))
        if "removed_by_id" not in columns:
            batch_op.add_column(sa.Column("removed_by_id", sa.Integer(), nullable=True))
        if "removal_reason" not in columns:
            batch_op.add_column(sa.Column("removal_reason", sa.String(length=500), nullable=True))

    # Some development SQLite databases were created from SQLAlchemy metadata
    # before Alembic 0025 was stamped, so the columns may already exist. Only
    # add the FK when it is still missing. batch_alter_table keeps this safe on
    # SQLite, which cannot add a foreign key with a plain ALTER TABLE statement.
    if not _has_removed_by_foreign_key():
        with op.batch_alter_table("resource") as batch_op:
            batch_op.create_foreign_key(
                "fk_resource_removed_by_id_user",
                "user",
                ["removed_by_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade():
    if _has_removed_by_foreign_key():
        with op.batch_alter_table("resource") as batch_op:
            foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys("resource")
            for foreign_key in foreign_keys:
                if (
                    foreign_key.get("constrained_columns") == ["removed_by_id"]
                    and foreign_key.get("referred_table") == "user"
                    and foreign_key.get("name")
                ):
                    batch_op.drop_constraint(foreign_key["name"], type_="foreignkey")
                    break

    columns = _resource_columns()
    with op.batch_alter_table("resource") as batch_op:
        if "removal_reason" in columns:
            batch_op.drop_column("removal_reason")
        if "removed_by_id" in columns:
            batch_op.drop_column("removed_by_id")
        if "removed_at" in columns:
            batch_op.drop_column("removed_at")
