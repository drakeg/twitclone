"""add reply moderation and contribution support

Revision ID: 20260901_0033
Revises: 20260901_0032
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0033"
down_revision = "20260901_0032"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("reply") as batch_op:
        batch_op.add_column(sa.Column("removed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("removed_by_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("removal_reason", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_reply_removed_by_id_user",
            "user",
            ["removed_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "reply_contribution",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reply_id", sa.Integer(), sa.ForeignKey("reply.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal", sa.String(length=20), nullable=False),
        sa.CheckConstraint("signal in ('helpful', 'thoughtful', 'context')", name="ck_reply_contribution_signal"),
        sa.UniqueConstraint("user_id", "reply_id", "signal", name="uq_reply_contribution_user_reply_signal"),
    )

    op.create_table(
        "reply_report",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("reply_id", sa.Integer(), sa.ForeignKey("reply.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.CheckConstraint("status in ('pending', 'dismissed', 'removed')", name="ck_reply_report_status"),
        sa.UniqueConstraint("reporter_id", "reply_id", name="uq_reply_report_reporter_reply"),
    )
    op.create_index("ix_reply_report_reply_id", "reply_report", ["reply_id"], unique=False)


def downgrade():
    op.drop_index("ix_reply_report_reply_id", table_name="reply_report")
    op.drop_table("reply_report")
    op.drop_table("reply_contribution")
    with op.batch_alter_table("reply") as batch_op:
        batch_op.drop_constraint("fk_reply_removed_by_id_user", type_="foreignkey")
        batch_op.drop_column("removal_reason")
        batch_op.drop_column("removed_by_id")
        batch_op.drop_column("removed_at")
