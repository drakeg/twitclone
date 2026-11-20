"""add reversible space archive state

Revision ID: 20261120_0043
Revises: 20261120_0042
"""

from alembic import op
import sqlalchemy as sa


revision = "20261120_0043"
down_revision = "20261120_0042"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("space") as batch_op:
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("archived_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_space_archived_by_id_user",
            "user",
            ["archived_by_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("space") as batch_op:
        batch_op.drop_constraint("fk_space_archived_by_id_user", type_="foreignkey")
        batch_op.drop_column("archived_by_id")
        batch_op.drop_column("archived_at")
