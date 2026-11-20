"""add space membership administration audit

Revision ID: 20261120_0040
Revises: 20260923_0039
"""

from alembic import op
import sqlalchemy as sa


revision = "20261120_0040"
down_revision = "20260923_0039"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_membership_action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("affected_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("previous_role", sa.String(length=20), nullable=True),
        sa.Column("new_role", sa.String(length=20), nullable=True),
        sa.Column("details", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action_type in ('ownership_transferred', 'role_changed', 'member_removed')",
            name="ck_space_membership_action_type",
        ),
        sa.CheckConstraint(
            "previous_role is null or previous_role in ('owner', 'moderator', 'member')",
            name="ck_space_membership_action_previous_role",
        ),
        sa.CheckConstraint(
            "new_role is null or new_role in ('owner', 'moderator', 'member')",
            name="ck_space_membership_action_new_role",
        ),
    )
    op.create_index("ix_space_membership_action_space_id", "space_membership_action", ["space_id"])
    op.create_index("ix_space_membership_action_actor_id", "space_membership_action", ["actor_id"])
    op.create_index(
        "ix_space_membership_action_affected_user_id",
        "space_membership_action",
        ["affected_user_id"],
    )


def downgrade():
    op.drop_index("ix_space_membership_action_affected_user_id", table_name="space_membership_action")
    op.drop_index("ix_space_membership_action_actor_id", table_name="space_membership_action")
    op.drop_index("ix_space_membership_action_space_id", table_name="space_membership_action")
    op.drop_table("space_membership_action")
