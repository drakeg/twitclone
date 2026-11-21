"""add Space event RSVPs

Revision ID: 20261121_0052
Revises: 20261121_0051
"""

from alembic import op
import sqlalchemy as sa


revision = "20261121_0052"
down_revision = "20261121_0051"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_event_rsvp",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("space_event.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "event_id",
            "user_id",
            name="uq_space_event_rsvp_event_user",
        ),
        sa.CheckConstraint(
            "status in ('going', 'maybe')",
            name="ck_space_event_rsvp_status",
        ),
    )
    op.create_index("ix_space_event_rsvp_event_id", "space_event_rsvp", ["event_id"])
    op.create_index("ix_space_event_rsvp_user_id", "space_event_rsvp", ["user_id"])


def downgrade():
    op.drop_index("ix_space_event_rsvp_user_id", table_name="space_event_rsvp")
    op.drop_index("ix_space_event_rsvp_event_id", table_name="space_event_rsvp")
    op.drop_table("space_event_rsvp")
