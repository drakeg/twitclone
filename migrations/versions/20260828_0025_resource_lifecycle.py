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


def upgrade():
    op.add_column("resource", sa.Column("removed_at", sa.DateTime(), nullable=True))
    op.add_column("resource", sa.Column("removed_by_id", sa.Integer(), nullable=True))
    op.add_column("resource", sa.Column("removal_reason", sa.String(length=500), nullable=True))
    op.create_foreign_key(
        "fk_resource_removed_by_id_user",
        "resource",
        "user",
        ["removed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_resource_removed_by_id_user", "resource", type_="foreignkey")
    op.drop_column("resource", "removal_reason")
    op.drop_column("resource", "removed_by_id")
    op.drop_column("resource", "removed_at")
