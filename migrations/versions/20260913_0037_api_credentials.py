"""add scoped API credentials

Revision ID: 20260913_0037
Revises: 20260907_0036
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_0037"
down_revision = "20260907_0036"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_credential",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("token_prefix", sa.String(length=16), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("scopes", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("length(label) between 1 and 80", name="ck_api_credential_label_length"),
        sa.UniqueConstraint("token_digest", name="uq_api_credential_token_digest"),
    )
    op.create_index("ix_api_credential_user_id", "api_credential", ["user_id"])


def downgrade():
    op.drop_index("ix_api_credential_user_id", table_name="api_credential")
    op.drop_table("api_credential")
