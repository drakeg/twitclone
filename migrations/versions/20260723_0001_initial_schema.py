"""Create the initial TwitClone schema.

Revision ID: 20260723_0001
Revises:
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa

revision = "20260723_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password", sa.String(length=150), nullable=False),
        sa.Column("bio", sa.String(length=300), nullable=True),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "follows",
        sa.Column("follower_id", sa.Integer(), nullable=False),
        sa.Column("followed_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["follower_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["followed_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("follower_id", "followed_id"),
    )
    op.create_table(
        "tweet",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.String(length=144), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("image", sa.String(length=100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_table(
        "direct_message",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.String(length=500), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("receiver_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sender_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["receiver_id"], ["user.id"]),
    )
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.String(length=200), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_table(
        "poll",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_table(
        "retweet",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tweet_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["tweet_id"], ["tweet.id"]),
    )
    op.create_table(
        "quote",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tweet_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(length=144), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["tweet_id"], ["tweet.id"]),
    )
    op.create_table(
        "bookmark",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tweet_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["tweet_id"], ["tweet.id"]),
    )
    op.create_table(
        "poll_option",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("option_text", sa.String(length=255), nullable=False),
        sa.Column("poll_id", sa.Integer(), nullable=False),
        sa.Column("votes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["poll_id"], ["poll.id"]),
    )
    op.create_table(
        "poll_vote",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("poll_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["poll_id"], ["poll.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["option_id"], ["poll_option.id"]),
    )


def downgrade():
    op.drop_table("poll_vote")
    op.drop_table("poll_option")
    op.drop_table("bookmark")
    op.drop_table("quote")
    op.drop_table("retweet")
    op.drop_table("poll")
    op.drop_table("notification")
    op.drop_table("direct_message")
    op.drop_table("tweet")
    op.drop_table("follows")
    op.drop_table("user")
