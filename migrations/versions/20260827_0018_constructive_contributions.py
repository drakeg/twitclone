"""add constructive contribution signals

Revision ID: 20260827_0018
Revises: 20260826_0017
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_0018"
down_revision = "20260826_0017"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "constructive_contribution",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tweet_id", sa.Integer(), sa.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal", sa.String(length=20), nullable=False),
        sa.CheckConstraint(
            "signal in ('helpful', 'thoughtful', 'context')",
            name="ck_constructive_contribution_signal",
        ),
        sa.UniqueConstraint(
            "user_id", "tweet_id", "signal",
            name="uq_constructive_contribution_user_tweet_signal",
        ),
    )


def downgrade():
    op.drop_table("constructive_contribution")
