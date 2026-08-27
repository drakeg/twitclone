"""add community fact context submissions

Revision ID: 20260827_0019
Revises: 20260827_0018
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_0019"
down_revision = "20260827_0018"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fact_context_submission",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tweet_id", sa.Integer(), sa.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitter_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim", sa.String(length=300), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("outcome", sa.String(length=20), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.CheckConstraint("status in ('pending', 'approved', 'rejected')", name="ck_fact_context_submission_status"),
        sa.CheckConstraint("outcome is null or outcome in ('context', 'disputed', 'outdated', 'correction')", name="ck_fact_context_submission_outcome"),
    )
    op.create_index("ix_fact_context_tweet_status", "fact_context_submission", ["tweet_id", "status"])


def downgrade():
    op.drop_index("ix_fact_context_tweet_status", table_name="fact_context_submission")
    op.drop_table("fact_context_submission")
