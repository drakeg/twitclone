"""add Space events

Revision ID: 20261121_0050
Revises: 20261121_0049
"""

from alembic import op
import sqlalchemy as sa


revision = "20261121_0050"
down_revision = "20261121_0049"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "space_id",
            sa.Integer(),
            sa.ForeignKey("space.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_space_event_space_id", "space_event", ["space_id"])
    op.create_index("ix_space_event_created_by_id", "space_event", ["created_by_id"])
    op.create_index("ix_space_event_starts_at", "space_event", ["starts_at"])


def downgrade():
    op.drop_index("ix_space_event_starts_at", table_name="space_event")
    op.drop_index("ix_space_event_created_by_id", table_name="space_event")
    op.drop_index("ix_space_event_space_id", table_name="space_event")
    op.drop_table("space_event")
