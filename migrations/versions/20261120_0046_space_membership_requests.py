"""add private Space membership requests

Revision ID: 20261120_0046
Revises: 20261120_0045
"""

from alembic import op
import sqlalchemy as sa


revision = "20261120_0046"
down_revision = "20261120_0045"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_membership_request",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint(
            "status in ('pending', 'approved', 'denied')",
            name="ck_space_membership_request_status",
        ),
    )
    op.create_index("ix_space_membership_request_space_id", "space_membership_request", ["space_id"])
    op.create_index("ix_space_membership_request_requester_id", "space_membership_request", ["requester_id"])
    op.create_index("ix_space_membership_request_resolved_by_id", "space_membership_request", ["resolved_by_id"])


def downgrade():
    op.drop_index("ix_space_membership_request_resolved_by_id", table_name="space_membership_request")
    op.drop_index("ix_space_membership_request_requester_id", table_name="space_membership_request")
    op.drop_index("ix_space_membership_request_space_id", table_name="space_membership_request")
    op.drop_table("space_membership_request")
