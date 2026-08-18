"""Track direct-message read state independently from notifications.

Revision ID: 20260818_0006
Revises: 20260815_0005
"""

import sqlalchemy as sa
from alembic import op

revision = "20260818_0006"
down_revision = "20260815_0005"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("direct_message") as batch_op:
        batch_op.add_column(
            sa.Column(
                "read",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("direct_message") as batch_op:
        batch_op.drop_column("read")
