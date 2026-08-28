"""add collaborative resource foundation

Revision ID: 20260828_0024
Revises: 20260828_0023
"""

from alembic import op
import sqlalchemy as sa


revision = "20260828_0024"
down_revision = "20260828_0023"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resource",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("current_revision_id", sa.Integer(), nullable=True),
        sa.Column("is_removed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_resource_owner_id", "resource", ["owner_id"])
    op.create_table(
        "resource_revision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resource.id", ondelete="CASCADE"), nullable=False),
        sa.Column("editor_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("change_note", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("resource_id", "revision_number", name="uq_resource_revision_number"),
    )
    op.create_index("ix_resource_revision_resource_id", "resource_revision", ["resource_id"])
    op.create_index("ix_resource_revision_editor_id", "resource_revision", ["editor_id"])
    op.create_table(
        "resource_topic",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resource.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topic.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("resource_id", "topic_id", name="uq_resource_topic_resource_topic"),
    )
    op.create_index("ix_resource_topic_resource_id", "resource_topic", ["resource_id"])
    op.create_index("ix_resource_topic_topic_id", "resource_topic", ["topic_id"])


def downgrade():
    op.drop_index("ix_resource_topic_topic_id", table_name="resource_topic")
    op.drop_index("ix_resource_topic_resource_id", table_name="resource_topic")
    op.drop_table("resource_topic")
    op.drop_index("ix_resource_revision_editor_id", table_name="resource_revision")
    op.drop_index("ix_resource_revision_resource_id", table_name="resource_revision")
    op.drop_table("resource_revision")
    op.drop_index("ix_resource_owner_id", table_name="resource")
    op.drop_table("resource")
