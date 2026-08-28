"""add explicit topic foundation

Revision ID: 20260828_0023
Revises: 20260827_0022
"""

from alembic import op
import sqlalchemy as sa


revision = "20260828_0023"
down_revision = "20260827_0022"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "topic",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_topic_slug"),
    )
    op.create_table(
        "tweet_topic",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tweet_id", sa.Integer(), sa.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topic.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("source in ('explicit', 'hashtag')", name="ck_tweet_topic_source"),
        sa.UniqueConstraint("tweet_id", "topic_id", name="uq_tweet_topic_tweet_topic"),
    )
    op.create_index("ix_tweet_topic_topic_id", "tweet_topic", ["topic_id"])
    op.create_index("ix_tweet_topic_tweet_id", "tweet_topic", ["tweet_id"])


def downgrade():
    op.drop_index("ix_tweet_topic_tweet_id", table_name="tweet_topic")
    op.drop_index("ix_tweet_topic_topic_id", table_name="tweet_topic")
    op.drop_table("tweet_topic")
    op.drop_table("topic")
