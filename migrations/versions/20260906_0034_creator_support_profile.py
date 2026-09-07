"""add creator support profile foundation

Revision ID: 20260906_0034
Revises: 20260901_0033
"""

from alembic import op
import sqlalchemy as sa


revision = "20260906_0034"
down_revision = "20260901_0033"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "creator_support_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("message", sa.String(length=280), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_creator_support_profile_user"),
    )


def downgrade():
    op.drop_table("creator_support_profile")
