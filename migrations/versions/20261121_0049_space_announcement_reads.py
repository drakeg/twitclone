"""add per-member Space announcement read state

Revision ID: 20261121_0049
Revises: 20261121_0048
"""

from alembic import op
import sqlalchemy as sa


revision = "20261121_0049"
down_revision = "20261121_0048"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_announcement_read",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "announcement_id",
            sa.Integer(),
            sa.ForeignKey("space_announcement.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "announcement_id",
            "user_id",
            name="uq_space_announcement_read_announcement_user",
        ),
    )
    op.create_index(
        "ix_space_announcement_read_announcement_id",
        "space_announcement_read",
        ["announcement_id"],
    )
    op.create_index(
        "ix_space_announcement_read_user_id",
        "space_announcement_read",
        ["user_id"],
    )


def downgrade():
    op.drop_index(
        "ix_space_announcement_read_user_id",
        table_name="space_announcement_read",
    )
    op.drop_index(
        "ix_space_announcement_read_announcement_id",
        table_name="space_announcement_read",
    )
    op.drop_table("space_announcement_read")
