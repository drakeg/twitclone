"""add email ownership verification status

Revision ID: 20260826_0016
Revises: 20260819_0015
"""

from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa


revision = "20260826_0016"
down_revision = "20260819_0015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_verification_status",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    now = datetime.now(UTC).replace(tzinfo=None)
    connection = op.get_bind()
    user_rows = connection.execute(sa.text("SELECT id FROM user")).fetchall()
    if user_rows:
        status = sa.table(
            "email_verification_status",
            sa.column("user_id", sa.Integer()),
            sa.column("verified_at", sa.DateTime()),
            sa.column("created_at", sa.DateTime()),
        )
        op.bulk_insert(
            status,
            [
                {"user_id": row[0], "verified_at": now, "created_at": now}
                for row in user_rows
            ],
        )


def downgrade():
    op.drop_table("email_verification_status")
