"""add persistent feed preference

Revision ID: 20260828_0026
Revises: 20260828_0025
"""

from alembic import op
import sqlalchemy as sa


revision = "20260828_0026"
down_revision = "20260828_0025"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_feed_preference",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("feed_mode", sa.String(length=20), nullable=False, server_default="all"),
        sa.CheckConstraint("feed_mode in ('all', 'following')", name="ck_user_feed_preference_mode"),
    )


def downgrade():
    op.drop_table("user_feed_preference")
