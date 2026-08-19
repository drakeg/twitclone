"""add Ripple Plus bookmark folders

Revision ID: 20260818_0013
Revises: 20260818_0012
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa

revision = '20260818_0013'
down_revision = '20260818_0012'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'bookmark_folder',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('user_id', 'name', name='uq_bookmark_folder_user_name'),
    )
    with op.batch_alter_table('bookmark') as batch_op:
        batch_op.add_column(sa.Column('folder_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_bookmark_folder_id_bookmark_folder',
            'bookmark_folder',
            ['folder_id'],
            ['id'],
        )


def downgrade():
    with op.batch_alter_table('bookmark') as batch_op:
        batch_op.drop_constraint('fk_bookmark_folder_id_bookmark_folder', type_='foreignkey')
        batch_op.drop_column('folder_id')
    op.drop_table('bookmark_folder')
