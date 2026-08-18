"""Track per-user direct-message deletion state.

Revision ID: 20260818_0007
Revises: 20260818_0006
"""

from alembic import op
import sqlalchemy as sa

revision = "20260818_0007"
down_revision = "20260818_0006"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("direct_message") as batch_op:
        batch_op.add_column(
            sa.Column(
                "deleted_by_sender",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "deleted_by_receiver",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("direct_message") as batch_op:
        batch_op.drop_column("deleted_by_receiver")
        batch_op.drop_column("deleted_by_sender")
