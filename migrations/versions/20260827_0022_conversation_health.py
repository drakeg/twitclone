"""add author-controlled conversation health state

Revision ID: 20260827_0022
Revises: 20260827_0021
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_0022"
down_revision = "20260827_0021"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tweet_conversation_state",
        sa.Column("tweet_id", sa.Integer(), sa.ForeignKey("tweet.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("tweet_conversation_state")
