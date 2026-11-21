"""add Space announcement lifecycle and audit

Revision ID: 20261121_0048
Revises: 20261121_0047
"""

from alembic import op
import sqlalchemy as sa


revision = "20261121_0048"
down_revision = "20261121_0047"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("space_announcement") as batch_op:
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_withdrawn",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("withdrawn_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("withdrawn_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_space_announcement_withdrawn_by_id_user",
            "user",
            ["withdrawn_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "space_announcement_action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "space_id",
            sa.Integer(),
            sa.ForeignKey("space.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "announcement_id",
            sa.Integer(),
            sa.ForeignKey("space_announcement.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column("previous_title", sa.String(length=120), nullable=True),
        sa.Column("new_title", sa.String(length=120), nullable=True),
        sa.Column("previous_body", sa.String(length=1000), nullable=True),
        sa.Column("new_body", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action_type in ('created', 'edited', 'withdrawn', 'restored')",
            name="ck_space_announcement_action_type",
        ),
    )
    op.create_index(
        "ix_space_announcement_action_space_id",
        "space_announcement_action",
        ["space_id"],
    )
    op.create_index(
        "ix_space_announcement_action_announcement_id",
        "space_announcement_action",
        ["announcement_id"],
    )
    op.create_index(
        "ix_space_announcement_action_actor_id",
        "space_announcement_action",
        ["actor_id"],
    )


def downgrade():
    op.drop_index(
        "ix_space_announcement_action_actor_id",
        table_name="space_announcement_action",
    )
    op.drop_index(
        "ix_space_announcement_action_announcement_id",
        table_name="space_announcement_action",
    )
    op.drop_index(
        "ix_space_announcement_action_space_id",
        table_name="space_announcement_action",
    )
    op.drop_table("space_announcement_action")

    with op.batch_alter_table("space_announcement") as batch_op:
        batch_op.drop_constraint(
            "fk_space_announcement_withdrawn_by_id_user",
            type_="foreignkey",
        )
        batch_op.drop_column("withdrawn_by_id")
        batch_op.drop_column("withdrawn_at")
        batch_op.drop_column("is_withdrawn")
        batch_op.drop_column("updated_at")
