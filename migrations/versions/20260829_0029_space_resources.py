"""add attributable space resource associations

Revision ID: 20260829_0029
Revises: 20260829_0028
"""

from alembic import op
import sqlalchemy as sa


revision = "20260829_0029"
down_revision = "20260829_0028"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "space_resource",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resource.id", ondelete="CASCADE"), nullable=False),
        sa.Column("linked_by_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("space_id", "resource_id", name="uq_space_resource_space_resource"),
    )
    op.create_index("ix_space_resource_space_id", "space_resource", ["space_id"])
    op.create_index("ix_space_resource_resource_id", "space_resource", ["resource_id"])
    op.create_index("ix_space_resource_linked_by_id", "space_resource", ["linked_by_id"])


def downgrade():
    op.drop_index("ix_space_resource_linked_by_id", table_name="space_resource")
    op.drop_index("ix_space_resource_resource_id", table_name="space_resource")
    op.drop_index("ix_space_resource_space_id", table_name="space_resource")
    op.drop_table("space_resource")
