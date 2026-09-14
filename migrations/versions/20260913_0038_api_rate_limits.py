"""add API rate-limit buckets

Revision ID: 20260913_0038
Revises: 20260913_0037
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_0038"
down_revision = "20260913_0037"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_rate_limit_bucket",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bucket_type", sa.String(length=40), nullable=False),
        sa.Column("subject_hash", sa.String(length=64), nullable=False),
        sa.Column("window_started_at", sa.DateTime(), nullable=False),
        sa.Column("window_expires_at", sa.DateTime(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("request_count >= 1", name="ck_api_rate_limit_request_count"),
        sa.UniqueConstraint(
            "bucket_type",
            "subject_hash",
            "window_started_at",
            name="uq_api_rate_limit_bucket_window",
        ),
    )
    op.create_index(
        "ix_api_rate_limit_bucket_window_expires_at",
        "api_rate_limit_bucket",
        ["window_expires_at"],
    )


def downgrade():
    op.drop_index(
        "ix_api_rate_limit_bucket_window_expires_at",
        table_name="api_rate_limit_bucket",
    )
    op.drop_table("api_rate_limit_bucket")
