"""add measured sustainability page visits

Revision ID: 20260907_0036
Revises: 20260907_0035
"""

from alembic import op
import sqlalchemy as sa


revision = "20260907_0036"
down_revision = "20260907_0035"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sustainability_page_visit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_type", sa.String(length=20), nullable=False),
        sa.Column("visitor_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("visitor_key", sa.String(length=80), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("page_type in ('support', 'membership')", name="ck_sustainability_page_visit_type"),
        sa.UniqueConstraint(
            "creator_user_id",
            "page_type",
            "visitor_key",
            "visit_date",
            name="uq_sustainability_page_visit_daily_visitor",
        ),
    )
    op.create_index(
        "ix_sustainability_page_visit_creator_date",
        "sustainability_page_visit",
        ["creator_user_id", "visit_date"],
    )


def downgrade():
    op.drop_index("ix_sustainability_page_visit_creator_date", table_name="sustainability_page_visit")
    op.drop_table("sustainability_page_visit")
