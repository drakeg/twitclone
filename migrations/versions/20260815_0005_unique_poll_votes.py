"""Enforce one vote per user and poll.

Revision ID: 20260815_0005
Revises: 20260815_0004
"""

from alembic import op

revision = "20260815_0005"
down_revision = "20260815_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "DELETE FROM poll_vote WHERE id NOT IN "
        "(SELECT MIN(id) FROM poll_vote GROUP BY poll_id, user_id)"
    )
    op.execute(
        "UPDATE poll_option SET votes = "
        "(SELECT COUNT(*) FROM poll_vote WHERE poll_vote.option_id = poll_option.id)"
    )
    with op.batch_alter_table("poll_vote") as batch_op:
        batch_op.create_unique_constraint(
            "uq_poll_vote_poll_user", ["poll_id", "user_id"]
        )


def downgrade():
    with op.batch_alter_table("poll_vote") as batch_op:
        batch_op.drop_constraint("uq_poll_vote_poll_user", type_="unique")
