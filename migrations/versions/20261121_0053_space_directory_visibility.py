"""add Space member directory visibility preference

Revision ID: 20261121_0053
Revises: 20261121_0052
"""

from alembic import op
import sqlalchemy as sa


revision = "20261121_0053"
down_revision = "20261121_0052"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("space_membership") as batch_op:
        batch_op.add_column(
            sa.Column(
                "directory_visible",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("space_membership") as batch_op:
        batch_op.drop_column("directory_visible")
