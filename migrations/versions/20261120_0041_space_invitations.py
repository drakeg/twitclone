"""add space invitations

Revision ID: 20261120_0041
Revises: 20261120_0040
"""

from alembic import op
import sqlalchemy as sa


revision = "20261120_0041"
down_revision = "20261120_0040"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_invitation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_by_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status in ('pending', 'accepted', 'declined', 'canceled')",
            name="ck_space_invitation_status",
        ),
    )
    op.create_index("ix_space_invitation_space_id", "space_invitation", ["space_id"])
    op.create_index("ix_space_invitation_invited_user_id", "space_invitation", ["invited_user_id"])
    op.create_index("ix_space_invitation_status", "space_invitation", ["status"])


def downgrade():
    op.drop_index("ix_space_invitation_status", table_name="space_invitation")
    op.drop_index("ix_space_invitation_invited_user_id", table_name="space_invitation")
    op.drop_index("ix_space_invitation_space_id", table_name="space_invitation")
    op.drop_table("space_invitation")
