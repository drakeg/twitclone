"""add space-scoped posts

Revision ID: 20260829_0028
Revises: 20260829_0027
"""

from alembic import op
import sqlalchemy as sa


revision = "20260829_0028"
down_revision = "20260829_0027"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_post",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tweet_id", sa.Integer(), sa.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tweet_id", name="uq_space_post_tweet"),
    )
    op.create_index("ix_space_post_space_id", "space_post", ["space_id"])
    op.create_index("ix_space_post_tweet_id", "space_post", ["tweet_id"])


def downgrade():
    op.drop_index("ix_space_post_tweet_id", table_name="space_post")
    op.drop_index("ix_space_post_space_id", table_name="space_post")
    op.drop_table("space_post")
