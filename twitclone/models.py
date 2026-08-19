"""Database models for Ripple.

This module owns the application's SQLAlchemy model definitions. All models use
the shared database extension from :mod:`twitclone.extensions` so migrations,
routes, tests, and future blueprints operate on one metadata registry.
"""

from datetime import UTC, datetime, timedelta

from flask_login import UserMixin

from twitclone.extensions import db


def _utcnow():
    """Return naive UTC for the existing database DateTime contract."""
    return datetime.now(UTC).replace(tzinfo=None)


class Follows(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class HashtagFollow(db.Model):
    __table_args__ = (db.UniqueConstraint('user_id', 'hashtag', name='uq_hashtag_follow_user_hashtag'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hashtag = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    user = db.relationship('User', back_populates='followed_hashtags')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.String(300))
    is_admin = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    identity_verified = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    verification_type = db.Column(db.String(40), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    community_guidelines_version = db.Column(db.String(20), nullable=True)
    community_guidelines_accepted_at = db.Column(db.DateTime, nullable=True)
    followed = db.relationship('User', secondary='follows', primaryjoin=(id == Follows.follower_id), secondaryjoin=(id == Follows.followed_id), backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    followed_hashtags = db.relationship('HashtagFollow', back_populates='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    bookmarks = db.relationship('Bookmark', back_populates='user', lazy=True)
    bookmark_folders = db.relationship('BookmarkFolder', back_populates='user', lazy=True, cascade='all, delete-orphan')
    verification_requests = db.relationship('VerificationRequest', foreign_keys='VerificationRequest.user_id', back_populates='user', lazy=True, cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', back_populates='user', lazy=True, cascade='all, delete-orphan')
    entitlements = db.relationship('Entitlement', back_populates='user', lazy=True, cascade='all, delete-orphan')

    def has_entitlement(self, key):
        now = _utcnow()
        return any(item.key == key and item.active and (item.expires_at is None or item.expires_at > now) for item in self.entitlements)

    @property
    def verified_badge_active(self):
        return self.identity_verified and self.has_entitlement('verified_badge')


class VerificationRequest(db.Model):
    __table_args__ = (
        db.CheckConstraint("verification_type in ('person', 'organization')", name='ck_verification_request_type'),
        db.CheckConstraint("status in ('pending', 'approved', 'rejected', 'revoked')", name='ck_verification_request_status'),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    verification_type = db.Column(db.String(40), nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    official_website = db.Column(db.String(500), nullable=True)
    supporting_information = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', server_default='pending')
    submitted_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], back_populates='verification_requests')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])


class Plan(db.Model):
    __table_args__ = (db.UniqueConstraint('key', name='uq_plan_key'),)
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD', server_default='USD')
    interval = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    entitlement_key = db.Column(db.String(80), nullable=False)
    subscriptions = db.relationship('Subscription', back_populates='plan', lazy=True)


class Subscription(db.Model):
    __table_args__ = (db.CheckConstraint("status in ('pending', 'active', 'past_due', 'canceled', 'expired')", name='ck_subscription_status'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    provider = db.Column(db.String(40), nullable=True)
    provider_customer_id = db.Column(db.String(255), nullable=True)
    provider_subscription_id = db.Column(db.String(255), nullable=True, unique=True)
    status = db.Column(db.String(20), nullable=False, default='pending', server_default='pending')
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)
    user = db.relationship('User', back_populates='subscriptions')
    plan = db.relationship('Plan', back_populates='subscriptions')


class Entitlement(db.Model):
    __table_args__ = (db.UniqueConstraint('user_id', 'key', name='uq_entitlement_user_key'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    key = db.Column(db.String(80), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    source = db.Column(db.String(40), nullable=False, default='subscription', server_default='subscription')
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    granted_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', back_populates='entitlements')
    subscription = db.relationship('Subscription')


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(144), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    original_image = db.Column(db.String(100), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    is_removed = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    removed_at = db.Column(db.DateTime, nullable=True)
    removed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('tweets', lazy=True))
    removed_by = db.relationship('User', foreign_keys=[removed_by_id])


class Retweet(db.Model):
    __table_args__ = (db.UniqueConstraint('user_id', 'tweet_id', name='uq_retweet_user_tweet'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    user = db.relationship('User', backref=db.backref('retweets', lazy=True))
    tweet = db.relationship('Tweet', backref=db.backref('retweets', lazy=True))


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    content = db.Column(db.String(144), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    is_removed = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    removed_at = db.Column(db.DateTime, nullable=True)
    removed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('quotes', lazy=True))
    tweet = db.relationship('Tweet', backref=db.backref('quotes', lazy=True))
    removed_by = db.relationship('User', foreign_keys=[removed_by_id])


class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    read = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    deleted_by_sender = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    deleted_by_receiver = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    read = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=True)
    tweet = db.relationship('Tweet', foreign_keys=[tweet_id])


class PostReport(db.Model):
    __table_args__ = (
        db.CheckConstraint("content_type in ('tweet', 'quote', 'poll')", name='ck_post_report_content_type'),
        db.CheckConstraint("status in ('pending', 'dismissed', 'removed')", name='ck_post_report_status'),
        db.UniqueConstraint('reporter_id', 'content_type', 'content_id', name='uq_post_report_reporter_content'),
    )
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending', server_default='pending')
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    author = db.relationship('User', foreign_keys=[author_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])


class BookmarkFolder(db.Model):
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_bookmark_folder_user_name'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    user = db.relationship('User', back_populates='bookmark_folders')
    bookmarks = db.relationship('Bookmark', back_populates='folder', lazy=True)


class Bookmark(db.Model):
    __table_args__ = (db.UniqueConstraint('user_id', 'tweet_id', name='uq_bookmark_user_tweet'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('bookmark_folder.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    user = db.relationship('User', back_populates='bookmarks')
    tweet = db.relationship('Tweet', backref='bookmarked_tweets')
    folder = db.relationship('BookmarkFolder', back_populates='bookmarks')


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    duration_days = db.Column(db.Integer, nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_removed = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)
    removed_at = db.Column(db.DateTime, nullable=True)
    removed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('polls', lazy=True))
    removed_by = db.relationship('User', foreign_keys=[removed_by_id])
    options = db.relationship('PollOption', backref='poll', lazy=True)

    @property
    def expires_at(self):
        return self.created_at + timedelta(days=self.duration_days, hours=self.duration_hours, minutes=self.duration_minutes)

    def is_active_at(self, now):
        return now < self.expires_at

    @property
    def is_active(self):
        return self.is_active_at(_utcnow())


class PollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(255), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    votes = db.Column(db.Integer, default=0)


class PollVote(db.Model):
    __table_args__ = (db.UniqueConstraint('user_id', 'poll_id', name='uq_poll_vote_user_poll'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_option.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('poll_votes', lazy=True))
    poll = db.relationship('Poll', backref=db.backref('vote_records', lazy=True, cascade='all, delete-orphan'))
    option = db.relationship('PollOption', backref=db.backref('vote_records', lazy=True))


class ScheduledPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(144), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    user = db.relationship('User', backref=db.backref('scheduled_posts', lazy=True))
