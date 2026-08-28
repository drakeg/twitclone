"""add fact context appeals

Revision ID: 20260827_0021
Revises: 20260827_0020
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_0021"
down_revision = "20260827_0020"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fact_context_appeal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("fact_context_submission.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appellant_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("proposed_context", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_outcome", sa.String(length=20), nullable=True),
        sa.Column("resolved_context", sa.Text(), nullable=True),
        sa.Column("resolved_source_url", sa.String(length=1000), nullable=True),
        sa.CheckConstraint("status in ('pending', 'upheld', 'revised', 'withdrawn')", name="ck_fact_context_appeal_status"),
        sa.CheckConstraint("resolved_outcome is null or resolved_outcome in ('context', 'disputed', 'outdated', 'correction')", name="ck_fact_context_appeal_outcome"),
    )
    op.create_index("ix_fact_context_appeal_submission_status", "fact_context_appeal", ["submission_id", "status"])


def downgrade():
    op.drop_index("ix_fact_context_appeal_submission_status", table_name="fact_context_appeal")
    op.drop_table("fact_context_appeal")
