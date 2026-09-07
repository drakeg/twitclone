"""add creator membership offering foundation

Revision ID: 20260907_0035
Revises: 20260906_0034
"""

from alembic import op
import sqlalchemy as sa


revision = "20260907_0035"
down_revision = "20260906_0034"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "creator_membership_offering",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("name", sa.String(length=80), nullable=True),
        sa.Column("description", sa.String(length=280), nullable=True),
        sa.Column("benefits", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_creator_membership_offering_user"),
    )


def downgrade():
    op.drop_table("creator_membership_offering")
