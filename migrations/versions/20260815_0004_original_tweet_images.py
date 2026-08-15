"""Track original Tweet image filenames.

Revision ID: 20260815_0004
Revises: 20260813_0003
"""

from alembic import op
import sqlalchemy as sa

revision = "20260815_0004"
down_revision = "20260813_0003"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tweet") as batch_op:
        batch_op.add_column(sa.Column("original_image", sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table("tweet") as batch_op:
        batch_op.drop_column("original_image")
