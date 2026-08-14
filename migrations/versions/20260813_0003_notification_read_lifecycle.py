"""Enforce the notification read lifecycle.

Revision ID: 20260813_0003
Revises: 20260813_0002
Create Date: 2026-08-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0003"
down_revision = "20260813_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text("UPDATE notification SET read = :unread WHERE read IS NULL").bindparams(
            unread=False
        )
    )
    with op.batch_alter_table("notification") as batch_op:
        batch_op.alter_column(
            "read",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )


def downgrade():
    with op.batch_alter_table("notification") as batch_op:
        batch_op.alter_column(
            "read",
            existing_type=sa.Boolean(),
            nullable=True,
            server_default=None,
        )
