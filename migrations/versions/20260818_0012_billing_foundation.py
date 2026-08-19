"""add billing and entitlement foundation

Revision ID: 20260818_0012
Revises: 20260818_0011
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa

revision = '20260818_0012'
down_revision = '20260818_0011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'plan',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key', sa.String(length=80), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('interval', sa.String(length=20), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('entitlement_key', sa.String(length=80), nullable=False),
        sa.UniqueConstraint('key', name='uq_plan_key'),
    )
    op.create_table(
        'subscription',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plan.id'), nullable=False),
        sa.Column('provider', sa.String(length=40), nullable=True),
        sa.Column('provider_customer_id', sa.String(length=255), nullable=True),
        sa.Column('provider_subscription_id', sa.String(length=255), nullable=True, unique=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("status in ('pending', 'active', 'past_due', 'canceled', 'expired')", name='ck_subscription_status'),
    )
    op.create_table(
        'entitlement',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('key', sa.String(length=80), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('source', sa.String(length=40), nullable=False, server_default='subscription'),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscription.id'), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'key', name='uq_entitlement_user_key'),
    )


def downgrade():
    op.drop_table('entitlement')
    op.drop_table('subscription')
    op.drop_table('plan')
