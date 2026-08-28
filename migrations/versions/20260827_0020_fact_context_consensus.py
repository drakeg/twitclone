"""add community assessments for fact context

Revision ID: 20260827_0020
Revises: 20260827_0019
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_0020"
down_revision = "20260827_0019"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fact_context_assessment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("fact_context_submission.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assessment", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "assessment in ('context', 'disputed', 'outdated', 'correction', 'insufficient')",
            name="ck_fact_context_assessment_value",
        ),
        sa.UniqueConstraint(
            "submission_id", "reviewer_id",
            name="uq_fact_context_assessment_submission_reviewer",
        ),
    )


def downgrade():
    op.drop_table("fact_context_assessment")
