"""Persistent feed preference companion model for Sprint 12."""

from twitclone.extensions import db


class UserFeedPreference(db.Model):
    __tablename__ = "user_feed_preference"
    __table_args__ = (
        db.CheckConstraint("feed_mode in ('all', 'following')", name="ck_user_feed_preference_mode"),
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    feed_mode = db.Column(db.String(20), nullable=False, default="all", server_default="all")

    user = db.relationship("User", backref=db.backref("feed_preference_record", uselist=False))


__all__ = ["UserFeedPreference"]
