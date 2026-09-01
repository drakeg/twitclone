"""add threaded reply relationships

Revision ID: 20260901_0032
Revises: 20260901_0031
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0032"
down_revision = "20260901_0031"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("reply") as batch_op:
        batch_op.add_column(sa.Column("parent_reply_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_reply_parent_reply_id_reply",
            "reply",
            ["parent_reply_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_reply_parent_reply_id", ["parent_reply_id"], unique=False)


def downgrade():
    with op.batch_alter_table("reply") as batch_op:
        batch_op.drop_index("ix_reply_parent_reply_id")
        batch_op.drop_constraint("fk_reply_parent_reply_id_reply", type_="foreignkey")
        batch_op.drop_column("parent_reply_id")
