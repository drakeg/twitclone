"""add conversation intent metadata

Revision ID: 20260826_0017
Revises: 20260826_0016
"""

from alembic import op
import sqlalchemy as sa


revision = "20260826_0017"
down_revision = "20260826_0016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tweet_conversation_intent",
        sa.Column(
            "tweet_id",
            sa.Integer(),
            sa.ForeignKey("tweet.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("intent", sa.String(length=20), nullable=False, server_default="open"),
        sa.CheckConstraint(
            "intent in ('open', 'question', 'advice', 'support', 'debate', 'sharing')",
            name="ck_tweet_conversation_intent_value",
        ),
    )


def downgrade():
    op.drop_table("tweet_conversation_intent")
