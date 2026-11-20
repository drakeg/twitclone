"""add space lifecycle audit

Revision ID: 20261120_0044
Revises: 20261120_0043
"""

from alembic import op
import sqlalchemy as sa


revision = "20261120_0044"
down_revision = "20261120_0043"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_lifecycle_action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("previous_name", sa.String(length=120), nullable=True),
        sa.Column("new_name", sa.String(length=120), nullable=True),
        sa.Column("previous_visibility", sa.String(length=20), nullable=True),
        sa.Column("new_visibility", sa.String(length=20), nullable=True),
        sa.Column("details", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action_type in ('settings_updated', 'archived', 'restored')",
            name="ck_space_lifecycle_action_type",
        ),
        sa.CheckConstraint(
            "previous_visibility is null or previous_visibility in ('public', 'private')",
            name="ck_space_lifecycle_previous_visibility",
        ),
        sa.CheckConstraint(
            "new_visibility is null or new_visibility in ('public', 'private')",
            name="ck_space_lifecycle_new_visibility",
        ),
    )
    op.create_index("ix_space_lifecycle_action_space_id", "space_lifecycle_action", ["space_id"])
    op.create_index("ix_space_lifecycle_action_actor_id", "space_lifecycle_action", ["actor_id"])


def downgrade():
    op.drop_index("ix_space_lifecycle_action_actor_id", table_name="space_lifecycle_action")
    op.drop_index("ix_space_lifecycle_action_space_id", table_name="space_lifecycle_action")
    op.drop_table("space_lifecycle_action")
