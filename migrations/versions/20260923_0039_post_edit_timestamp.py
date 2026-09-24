"""add original post edit timestamp

Revision ID: 20260923_0039
Revises: 20260913_0038
"""

from alembic import op
import sqlalchemy as sa


revision = "20260923_0039"
down_revision = "20260913_0038"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tweet") as batch_op:
        batch_op.add_column(sa.Column("edited_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("tweet") as batch_op:
        batch_op.drop_column("edited_at")
