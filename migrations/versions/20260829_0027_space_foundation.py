"""add community space foundation

Revision ID: 20260829_0027
Revises: 20260828_0026
"""

from alembic import op
import sqlalchemy as sa


revision = "20260829_0027"
down_revision = "20260828_0026"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="public"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_space_slug"),
        sa.CheckConstraint("visibility in ('public')", name="ck_space_visibility"),
    )
    op.create_index("ix_space_owner_id", "space", ["owner_id"])
    op.create_table(
        "space_membership",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("space_id", "user_id", name="uq_space_membership_space_user"),
        sa.CheckConstraint("role in ('owner', 'member')", name="ck_space_membership_role"),
    )
    op.create_index("ix_space_membership_space_id", "space_membership", ["space_id"])
    op.create_index("ix_space_membership_user_id", "space_membership", ["user_id"])


def downgrade():
    op.drop_index("ix_space_membership_user_id", table_name="space_membership")
    op.drop_index("ix_space_membership_space_id", table_name="space_membership")
    op.drop_table("space_membership")
    op.drop_index("ix_space_owner_id", table_name="space")
    op.drop_table("space")
