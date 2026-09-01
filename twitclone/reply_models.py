"""Persistent public reply model for Sprint 14."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Reply(db.Model):
    __tablename__ = "reply"

    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.String(144), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    is_removed = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())

    tweet = db.relationship("Tweet", backref=db.backref("public_replies", lazy=True, cascade="all, delete-orphan"))
    user = db.relationship("User", backref=db.backref("public_replies", lazy=True))


__all__ = ["Reply"]
