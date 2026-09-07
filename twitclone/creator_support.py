"""Creator support profile foundation for Sprint 15.

This module intentionally stores creator-authored support context only. It does
not process payments, grant reach, or alter moderation/reputation behavior.
"""

from datetime import UTC, datetime

from twitclone.extensions import db

MAX_SUPPORT_MESSAGE_LENGTH = 280


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class CreatorSupportProfile(db.Model):
    __tablename__ = "creator_support_profile"
    __table_args__ = (db.UniqueConstraint("user_id", name="uq_creator_support_profile_user"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    message = db.Column(db.String(MAX_SUPPORT_MESSAGE_LENGTH), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    user = db.relationship("User", backref=db.backref("creator_support_profile", uselist=False))


def normalized_support_message(value):
    message = (value or "").strip()
    if not message:
        return None
    return message[:MAX_SUPPORT_MESSAGE_LENGTH]


__all__ = ["CreatorSupportProfile", "MAX_SUPPORT_MESSAGE_LENGTH", "normalized_support_message"]
