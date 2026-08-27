"""Persistence model for Ripple conversation intent metadata."""

from twitclone.extensions import db


class TweetConversationIntent(db.Model):
    __tablename__ = "tweet_conversation_intent"

    tweet_id = db.Column(
        db.Integer,
        db.ForeignKey("tweet.id", ondelete="CASCADE"),
        primary_key=True,
    )
    intent = db.Column(db.String(20), nullable=False, default="open", server_default="open")

    tweet = db.relationship(
        "Tweet",
        backref=db.backref(
            "conversation_intent_record",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )


__all__ = ["TweetConversationIntent"]
