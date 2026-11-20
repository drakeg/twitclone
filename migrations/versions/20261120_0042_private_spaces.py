"""allow private spaces

Revision ID: 20261120_0042
Revises: 20261120_0041
"""

from alembic import op


revision = "20261120_0042"
down_revision = "20261120_0041"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("space") as batch_op:
        batch_op.drop_constraint("ck_space_visibility", type_="check")
        batch_op.create_check_constraint(
            "ck_space_visibility",
            "visibility in ('public', 'private')",
        )


def downgrade():
    with op.batch_alter_table("space") as batch_op:
        batch_op.drop_constraint("ck_space_visibility", type_="check")
        batch_op.create_check_constraint(
            "ck_space_visibility",
            "visibility in ('public')",
        )
