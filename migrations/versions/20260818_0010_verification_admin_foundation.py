"""add verification and admin foundation

Revision ID: 20260818_0010
Revises: 20260818_0009
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa


revision = '20260818_0010'
down_revision = '20260818_0009'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('identity_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('verification_type', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('verified_at', sa.DateTime(), nullable=True))

    op.create_table(
        'verification_request',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('verification_type', sa.String(length=40), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('official_website', sa.String(length=500), nullable=True),
        sa.Column('supporting_information', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.CheckConstraint("verification_type in ('person', 'organization')", name='ck_verification_request_type'),
        sa.CheckConstraint("status in ('pending', 'approved', 'rejected', 'revoked')", name='ck_verification_request_status'),
    )


def downgrade():
    op.drop_table('verification_request')
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('verified_at')
        batch_op.drop_column('verification_type')
        batch_op.drop_column('identity_verified')
        batch_op.drop_column('is_super_admin')
        batch_op.drop_column('is_admin')
