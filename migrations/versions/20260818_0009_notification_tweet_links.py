"""Link activity notifications to relevant posts.

Revision ID: 20260818_0009
Revises: 20260818_0008
"""

from alembic import op
import sqlalchemy as sa

revision = "20260818_0009"
down_revision = "20260818_0008"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("notification") as batch_op:
        batch_op.add_column(sa.Column("tweet_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_notification_tweet_id_tweet", "tweet", ["tweet_id"], ["id"]
        )


def downgrade():
    with op.batch_alter_table("notification") as batch_op:
        batch_op.drop_constraint("fk_notification_tweet_id_tweet", type_="foreignkey")
        batch_op.drop_column("tweet_id")
