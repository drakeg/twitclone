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


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.String(300))
    followed = db.relationship(
        'User',
        secondary='follows',
        primaryjoin=(id == Follows.follower_id),
        secondaryjoin=(id == Follows.followed_id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic',
    )
    notifications = db.relationship('Notification', backref='user', lazy=True)
    bookmarks = db.relationship('Bookmark', back_populates='user', lazy=True)


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(144), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    original_image = db.Column(db.String(100), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref=db.backref('tweets', lazy=True))


class Retweet(db.Model):
    __table_args__ = (
        db.UniqueConstraint('user_id', 'tweet_id', name='uq_retweet_user_tweet'),
    )

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
    user = db.relationship('User', backref=db.backref('quotes', lazy=True))
    tweet = db.relationship('Tweet', backref=db.backref('quotes', lazy=True))


class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    read = db.Column(
        db.Boolean, default=False, server_default=db.false(), nullable=False
    )


class Bookmark(db.Model):
    __table_args__ = (
        db.UniqueConstraint('user_id', 'tweet_id', name='uq_bookmark_user_tweet'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    user = db.relationship('User', back_populates='bookmarks')
    tweet = db.relationship('Tweet', backref='bookmarked_tweets')


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    duration_days = db.Column(db.Integer, nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('polls', lazy=True))
    options = db.relationship('PollOption', backref='poll', lazy=True)

    @property
    def expires_at(self):
        return self.created_at + timedelta(
            days=self.duration_days,
            hours=self.duration_hours,
            minutes=self.duration_minutes,
        )

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
    __table_args__ = (
        db.UniqueConstraint('poll_id', 'user_id', name='uq_poll_vote_poll_user'),
    )

    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_option.id'), nullable=False)


__all__ = [
    'Bookmark',
    'DirectMessage',
    'Follows',
    'Notification',
    'Poll',
    'PollOption',
    'PollVote',
    'Quote',
    'Retweet',
    'Tweet',
    'User',
]
