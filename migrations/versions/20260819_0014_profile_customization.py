"""add Ripple+ profile customization

Revision ID: 20260819_0014
Revises: 20260818_0013
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa

revision = '20260819_0014'
down_revision = '20260818_0013'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('profile_theme', sa.String(length=20), nullable=False, server_default='ripple'))
        batch_op.add_column(sa.Column('profile_banner', sa.String(length=160), nullable=True))


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('profile_banner')
        batch_op.drop_column('profile_theme')
