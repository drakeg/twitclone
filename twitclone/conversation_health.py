"""Author-controlled conversation health state for Ripple posts."""

from datetime import UTC, datetime

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user, login_required

from twitclone.community import community_blueprint
from twitclone.extensions import db
from twitclone.models import Tweet


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class TweetConversationState(db.Model):
    __tablename__ = "tweet_conversation_state"

    tweet_id = db.Column(
        db.Integer,
        db.ForeignKey("tweet.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_closed = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    is_resolved = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    tweet = db.relationship(
        "Tweet",
        backref=db.backref(
            "conversation_state_record",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )


def conversation_state(tweet):
    record = tweet.conversation_state_record
    return {
        "is_closed": bool(record and record.is_closed),
        "is_resolved": bool(record and record.is_resolved),
    }


def _state_record(tweet):
    record = tweet.conversation_state_record
    if record is None:
        record = TweetConversationState(tweet_id=tweet.id)
        db.session.add(record)
    return record


@community_blueprint.before_app_request
def enforce_closed_conversations():
    """Block new quote responses even when an old/direct quote URL is used."""
    if request.endpoint != "quote" or not current_user.is_authenticated:
        return None
    tweet_id = (request.view_args or {}).get("tweet_id")
    if tweet_id is None:
        return None
    tweet = db.session.get(Tweet, tweet_id)
    if tweet is None or tweet.is_removed:
        return None
    if conversation_state(tweet)["is_closed"]:
        flash("The author has closed this conversation to new quote responses.", "info")
        return redirect(url_for("post_detail", tweet_id=tweet.id))
    return None


@community_blueprint.route("/post/<int:tweet_id>/conversation-state", methods=["POST"])
@login_required
def update_conversation_state(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id)
    if tweet.is_removed:
        abort(404)
    if tweet.user_id != current_user.id:
        abort(403)

    action = (request.form.get("action") or "").strip().lower()
    record = _state_record(tweet)
    if action == "close":
        record.is_closed = True
        message = "Conversation closed to new quote responses. Existing responses remain visible."
    elif action == "reopen":
        record.is_closed = False
        message = "Conversation reopened to new quote responses."
    elif action == "resolve":
        record.is_resolved = True
        message = "Conversation marked answered/resolved."
    elif action == "unresolve":
        record.is_resolved = False
        message = "Answered/resolved status cleared."
    else:
        abort(400)

    record.updated_at = _utcnow()
    db.session.commit()
    flash(message, "success")
    return redirect(url_for("post_detail", tweet_id=tweet.id))


__all__ = ["TweetConversationState", "conversation_state"]
