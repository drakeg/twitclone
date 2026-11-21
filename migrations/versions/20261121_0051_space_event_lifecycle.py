"""add Space event lifecycle and audit

Revision ID: 20261121_0051
Revises: 20261121_0050
"""

from alembic import op
import sqlalchemy as sa


revision = "20261121_0051"
down_revision = "20261121_0050"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("space_event") as batch_op:
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_canceled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("canceled_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("canceled_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_space_event_canceled_by_id_user",
            "user",
            ["canceled_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "space_event_action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("space_event.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column("previous_title", sa.String(length=120), nullable=True),
        sa.Column("new_title", sa.String(length=120), nullable=True),
        sa.Column("previous_description", sa.String(length=1000), nullable=True),
        sa.Column("new_description", sa.String(length=1000), nullable=True),
        sa.Column("previous_location", sa.String(length=200), nullable=True),
        sa.Column("new_location", sa.String(length=200), nullable=True),
        sa.Column("previous_starts_at", sa.DateTime(), nullable=True),
        sa.Column("new_starts_at", sa.DateTime(), nullable=True),
        sa.Column("previous_timezone", sa.String(length=64), nullable=True),
        sa.Column("new_timezone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action_type in ('created', 'edited', 'canceled', 'restored')",
            name="ck_space_event_action_type",
        ),
    )
    op.create_index("ix_space_event_action_space_id", "space_event_action", ["space_id"])
    op.create_index("ix_space_event_action_event_id", "space_event_action", ["event_id"])
    op.create_index("ix_space_event_action_actor_id", "space_event_action", ["actor_id"])


def downgrade():
    op.drop_index("ix_space_event_action_actor_id", table_name="space_event_action")
    op.drop_index("ix_space_event_action_event_id", table_name="space_event_action")
    op.drop_index("ix_space_event_action_space_id", table_name="space_event_action")
    op.drop_table("space_event_action")

    with op.batch_alter_table("space_event") as batch_op:
        batch_op.drop_constraint(
            "fk_space_event_canceled_by_id_user",
            type_="foreignkey",
        )
        batch_op.drop_column("canceled_by_id")
        batch_op.drop_column("canceled_at")
        batch_op.drop_column("is_canceled")
        batch_op.drop_column("updated_at")
