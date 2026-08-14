"""Prevent duplicate social relationship records.

Revision ID: 20260813_0002
Revises: 20260723_0001
Create Date: 2026-08-13
"""

from alembic import op


revision = "20260813_0002"
down_revision = "20260723_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "DELETE FROM retweet WHERE id NOT IN "
        "(SELECT MIN(id) FROM retweet GROUP BY user_id, tweet_id)"
    )
    op.execute(
        "DELETE FROM bookmark WHERE id NOT IN "
        "(SELECT MIN(id) FROM bookmark GROUP BY user_id, tweet_id)"
    )
    with op.batch_alter_table("retweet") as batch_op:
        batch_op.create_unique_constraint(
            "uq_retweet_user_tweet", ["user_id", "tweet_id"]
        )
    with op.batch_alter_table("bookmark") as batch_op:
        batch_op.create_unique_constraint(
            "uq_bookmark_user_tweet", ["user_id", "tweet_id"]
        )


def downgrade():
    with op.batch_alter_table("bookmark") as batch_op:
        batch_op.drop_constraint("uq_bookmark_user_tweet", type_="unique")
    with op.batch_alter_table("retweet") as batch_op:
        batch_op.drop_constraint("uq_retweet_user_tweet", type_="unique")
