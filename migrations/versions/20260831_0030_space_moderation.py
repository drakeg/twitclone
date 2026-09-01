"""add space moderation roles, local visibility, audit, and appeals

Revision ID: 20260831_0030
Revises: 20260829_0029
"""

from alembic import op
import sqlalchemy as sa


revision = "20260831_0030"
down_revision = "20260829_0029"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("space_membership") as batch_op:
        batch_op.drop_constraint("ck_space_membership_role", type_="check")
        batch_op.create_check_constraint(
            "ck_space_membership_role",
            "role in ('owner', 'moderator', 'member')",
        )

    with op.batch_alter_table("space_post") as batch_op:
        batch_op.add_column(sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("hidden_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("hidden_by_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("hidden_reason", sa.String(length=500), nullable=True))
        batch_op.create_foreign_key(
            "fk_space_post_hidden_by_id_user",
            "user",
            ["hidden_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("space_resource") as batch_op:
        batch_op.add_column(sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("hidden_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("hidden_by_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("hidden_reason", sa.String(length=500), nullable=True))
        batch_op.create_foreign_key(
            "fk_space_resource_hidden_by_id_user",
            "user",
            ["hidden_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "space_moderation_action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("affected_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action_type in ('hide_post', 'restore_post', 'hide_resource', 'restore_resource', 'promote_moderator', 'demote_moderator')",
            name="ck_space_moderation_action_type",
        ),
        sa.CheckConstraint(
            "target_type in ('post', 'resource', 'membership')",
            name="ck_space_moderation_target_type",
        ),
    )
    op.create_index("ix_space_moderation_action_space_id", "space_moderation_action", ["space_id"])
    op.create_index("ix_space_moderation_action_actor_id", "space_moderation_action", ["actor_id"])
    op.create_index("ix_space_moderation_action_affected_user_id", "space_moderation_action", ["affected_user_id"])

    op.create_table(
        "space_moderation_appeal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_id", sa.Integer(), sa.ForeignKey("space_moderation_action.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rationale", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolution_note", sa.String(length=500), nullable=True),
        sa.UniqueConstraint("action_id", name="uq_space_moderation_appeal_action"),
        sa.CheckConstraint("status in ('pending', 'approved', 'denied')", name="ck_space_moderation_appeal_status"),
    )
    op.create_index("ix_space_moderation_appeal_space_id", "space_moderation_appeal", ["space_id"])
    op.create_index("ix_space_moderation_appeal_requester_id", "space_moderation_appeal", ["requester_id"])


def downgrade():
    op.drop_index("ix_space_moderation_appeal_requester_id", table_name="space_moderation_appeal")
    op.drop_index("ix_space_moderation_appeal_space_id", table_name="space_moderation_appeal")
    op.drop_table("space_moderation_appeal")

    op.drop_index("ix_space_moderation_action_affected_user_id", table_name="space_moderation_action")
    op.drop_index("ix_space_moderation_action_actor_id", table_name="space_moderation_action")
    op.drop_index("ix_space_moderation_action_space_id", table_name="space_moderation_action")
    op.drop_table("space_moderation_action")

    with op.batch_alter_table("space_resource") as batch_op:
        batch_op.drop_constraint("fk_space_resource_hidden_by_id_user", type_="foreignkey")
        batch_op.drop_column("hidden_reason")
        batch_op.drop_column("hidden_by_id")
        batch_op.drop_column("hidden_at")
        batch_op.drop_column("is_hidden")

    with op.batch_alter_table("space_post") as batch_op:
        batch_op.drop_constraint("fk_space_post_hidden_by_id_user", type_="foreignkey")
        batch_op.drop_column("hidden_reason")
        batch_op.drop_column("hidden_by_id")
        batch_op.drop_column("hidden_at")
        batch_op.drop_column("is_hidden")

    with op.batch_alter_table("space_membership") as batch_op:
        batch_op.drop_constraint("ck_space_membership_role", type_="check")
        batch_op.create_check_constraint(
            "ck_space_membership_role",
            "role in ('owner', 'member')",
        )
