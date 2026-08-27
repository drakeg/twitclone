"""Persistence for constructive feedback on Ripple posts."""

from twitclone.extensions import db


class ConstructiveContribution(db.Model):
    __tablename__ = "constructive_contribution"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "tweet_id", "signal", name="uq_constructive_contribution_user_tweet_signal"
        ),
        db.CheckConstraint(
            "signal in ('helpful', 'thoughtful', 'context')",
            name="ck_constructive_contribution_signal",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False)
    signal = db.Column(db.String(20), nullable=False)

    user = db.relationship("User")
    tweet = db.relationship("Tweet", backref=db.backref("constructive_contributions", cascade="all, delete-orphan"))


__all__ = ["ConstructiveContribution"]
