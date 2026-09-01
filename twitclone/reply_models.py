"""Persistent public reply models for Sprint 14."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Reply(db.Model):
    __tablename__ = "reply"

    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_reply_id = db.Column(db.Integer, db.ForeignKey("reply.id", ondelete="CASCADE"), nullable=True, index=True)
    content = db.Column(db.String(144), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    is_removed = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    removed_at = db.Column(db.DateTime, nullable=True)
    removed_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)

    tweet = db.relationship("Tweet", backref=db.backref("public_replies", lazy=True, cascade="all, delete-orphan"))
    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("public_replies", lazy=True))
    removed_by = db.relationship("User", foreign_keys=[removed_by_id])
    parent = db.relationship(
        "Reply",
        remote_side=[id],
        backref=db.backref("children", lazy=True),
        foreign_keys=[parent_reply_id],
    )


class ReplyContribution(db.Model):
    __tablename__ = "reply_contribution"
    __table_args__ = (
        db.UniqueConstraint("user_id", "reply_id", "signal", name="uq_reply_contribution_user_reply_signal"),
        db.CheckConstraint("signal in ('helpful', 'thoughtful', 'context')", name="ck_reply_contribution_signal"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    reply_id = db.Column(db.Integer, db.ForeignKey("reply.id", ondelete="CASCADE"), nullable=False)
    signal = db.Column(db.String(20), nullable=False)

    user = db.relationship("User")
    reply = db.relationship("Reply", backref=db.backref("constructive_contributions", cascade="all, delete-orphan"))


__all__ = ["Reply", "ReplyContribution"]
