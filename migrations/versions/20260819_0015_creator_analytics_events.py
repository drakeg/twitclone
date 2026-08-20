"""add creator analytics event tracking

Revision ID: 20260819_0015
Revises: 20260819_0014
"""

from alembic import op
import sqlalchemy as sa

revision = '20260819_0015'
down_revision = '20260819_0014'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'post_impression',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tweet_id', sa.Integer(), sa.ForeignKey('tweet.id'), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('viewer_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('viewer_key', sa.String(length=80), nullable=False),
        sa.Column('impression_date', sa.Date(), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('tweet_id', 'viewer_key', 'impression_date', name='uq_post_impression_daily_viewer'),
    )
    op.create_index('ix_post_impression_author_date', 'post_impression', ['author_id', 'impression_date'])
    op.create_table(
        'profile_visit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profile_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('visitor_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('visitor_key', sa.String(length=80), nullable=False),
        sa.Column('visit_date', sa.Date(), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('profile_user_id', 'visitor_key', 'visit_date', name='uq_profile_visit_daily_visitor'),
    )
    op.create_index('ix_profile_visit_profile_date', 'profile_visit', ['profile_user_id', 'visit_date'])
    op.create_table(
        'follower_snapshot',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('follower_count', sa.Integer(), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('user_id', 'snapshot_date', name='uq_follower_snapshot_user_date'),
    )


def downgrade():
    op.drop_table('follower_snapshot')
    op.drop_index('ix_profile_visit_profile_date', table_name='profile_visit')
    op.drop_table('profile_visit')
    op.drop_index('ix_post_impression_author_date', table_name='post_impression')
    op.drop_table('post_impression')
