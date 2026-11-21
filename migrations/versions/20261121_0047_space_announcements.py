"""add Space announcements

Revision ID: 20261121_0047
Revises: 20261120_0046
"""

from alembic import op
import sqlalchemy as sa


revision = "20261121_0047"
down_revision = "20261120_0046"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_announcement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "space_id",
            sa.Integer(),
            sa.ForeignKey("space.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_space_announcement_space_id",
        "space_announcement",
        ["space_id"],
    )
    op.create_index(
        "ix_space_announcement_author_id",
        "space_announcement",
        ["author_id"],
    )


def downgrade():
    op.drop_index("ix_space_announcement_author_id", table_name="space_announcement")
    op.drop_index("ix_space_announcement_space_id", table_name="space_announcement")
    op.drop_table("space_announcement")
