"""add community standards and moderation

Revision ID: 20260818_0011
Revises: 20260818_0010
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa


revision = '20260818_0011'
down_revision = '20260818_0010'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('community_guidelines_version', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('community_guidelines_accepted_at', sa.DateTime(), nullable=True))

    for table_name in ('tweet', 'quote', 'poll'):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column('is_removed', sa.Boolean(), nullable=False, server_default=sa.false()))
            batch_op.add_column(sa.Column('removed_at', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('removed_by_id', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('removal_reason', sa.Text(), nullable=True))
            batch_op.create_foreign_key(
                f'fk_{table_name}_removed_by_id_user', 'user', ['removed_by_id'], ['id']
            )

    op.create_table(
        'post_report',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('reporter_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=40), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.CheckConstraint("content_type in ('tweet', 'quote', 'poll')", name='ck_post_report_content_type'),
        sa.CheckConstraint("status in ('pending', 'dismissed', 'removed')", name='ck_post_report_status'),
        sa.UniqueConstraint('reporter_id', 'content_type', 'content_id', name='uq_post_report_reporter_content'),
    )


def downgrade():
    op.drop_table('post_report')
    for table_name in ('poll', 'quote', 'tweet'):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(f'fk_{table_name}_removed_by_id_user', type_='foreignkey')
            batch_op.drop_column('removal_reason')
            batch_op.drop_column('removed_by_id')
            batch_op.drop_column('removed_at')
            batch_op.drop_column('is_removed')

    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('community_guidelines_accepted_at')
        batch_op.drop_column('community_guidelines_version')
