"""Persistent measurement models for Creator Pro analytics."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class PostImpression(db.Model):
    __table_args__ = (
        db.UniqueConstraint('tweet_id', 'viewer_key', 'impression_date', name='uq_post_impression_daily_viewer'),
    )
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    viewer_key = db.Column(db.String(80), nullable=False)
    impression_date = db.Column(db.Date, nullable=False)
    first_seen_at = db.Column(db.DateTime, nullable=False, default=_utcnow)


class ProfileVisit(db.Model):
    __table_args__ = (
        db.UniqueConstraint('profile_user_id', 'visitor_key', 'visit_date', name='uq_profile_visit_daily_visitor'),
    )
    id = db.Column(db.Integer, primary_key=True)
    profile_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    visitor_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    visitor_key = db.Column(db.String(80), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    first_seen_at = db.Column(db.DateTime, nullable=False, default=_utcnow)


class FollowerSnapshot(db.Model):
    __table_args__ = (
        db.UniqueConstraint('user_id', 'snapshot_date', name='uq_follower_snapshot_user_date'),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    snapshot_date = db.Column(db.Date, nullable=False)
    follower_count = db.Column(db.Integer, nullable=False)
    captured_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
