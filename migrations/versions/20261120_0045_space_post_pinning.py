"""add Space conversation pinning and curation audit

Revision ID: 20261120_0045
Revises: 20261120_0044
"""

from alembic import op
import sqlalchemy as sa


revision = "20261120_0045"
down_revision = "20261120_0044"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("space_post") as batch_op:
        batch_op.add_column(sa.Column("pinned_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("pinned_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_space_post_pinned_by_id_user",
            "user",
            ["pinned_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "space_curation_action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("space_post_id", sa.Integer(), sa.ForeignKey("space_post.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("details", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action_type in ('pin_post', 'unpin_post')",
            name="ck_space_curation_action_type",
        ),
    )
    op.create_index("ix_space_curation_action_space_id", "space_curation_action", ["space_id"])
    op.create_index("ix_space_curation_action_space_post_id", "space_curation_action", ["space_post_id"])
    op.create_index("ix_space_curation_action_actor_id", "space_curation_action", ["actor_id"])


def downgrade():
    op.drop_index("ix_space_curation_action_actor_id", table_name="space_curation_action")
    op.drop_index("ix_space_curation_action_space_post_id", table_name="space_curation_action")
    op.drop_index("ix_space_curation_action_space_id", table_name="space_curation_action")
    op.drop_table("space_curation_action")

    with op.batch_alter_table("space_post") as batch_op:
        batch_op.drop_constraint("fk_space_post_pinned_by_id_user", type_="foreignkey")
        batch_op.drop_column("pinned_by_id")
        batch_op.drop_column("pinned_at")
