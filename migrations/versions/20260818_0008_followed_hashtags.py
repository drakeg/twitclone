"""Add followed hashtags.

Revision ID: 20260818_0008
Revises: 20260818_0007
"""

from alembic import op
import sqlalchemy as sa

revision = "20260818_0008"
down_revision = "20260818_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hashtag_follow",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hashtag", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "hashtag", name="uq_hashtag_follow_user_hashtag"),
    )


def downgrade():
    op.drop_table("hashtag_follow")
