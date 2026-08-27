"""add conversation intent to posts

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
    with op.batch_alter_table("tweet") as batch_op:
        batch_op.add_column(
            sa.Column(
                "conversation_intent",
                sa.String(length=20),
                nullable=False,
                server_default="open",
            )
        )
        batch_op.create_check_constraint(
            "ck_tweet_conversation_intent",
            "conversation_intent in ('open', 'question', 'advice', 'support', 'debate', 'sharing')",
        )


def downgrade():
    with op.batch_alter_table("tweet") as batch_op:
        batch_op.drop_constraint("ck_tweet_conversation_intent", type_="check")
        batch_op.drop_column("conversation_intent")
