"""add persistent public replies

Revision ID: 20260901_0031
Revises: 20260831_0030
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0031"
down_revision = "20260831_0030"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reply",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tweet_id", sa.Integer(), sa.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.String(length=144), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_removed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_reply_tweet_id", "reply", ["tweet_id"])
    op.create_index("ix_reply_user_id", "reply", ["user_id"])


def downgrade():
    op.drop_index("ix_reply_user_id", table_name="reply")
    op.drop_index("ix_reply_tweet_id", table_name="reply")
    op.drop_table("reply")
