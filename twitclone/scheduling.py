"""Idempotent scheduled-Tweet publication."""

from datetime import datetime

from twitclone.extensions import db
from twitclone.models import Tweet


def publish_due_tweets(*, now=None):
    now = now or datetime.utcnow()
    due_tweets = Tweet.query.filter(
        Tweet.scheduled_at.is_not(None), Tweet.scheduled_at <= now
    ).all()
    for tweet in due_tweets:
        tweet.timestamp = tweet.scheduled_at
        tweet.scheduled_at = None
    if due_tweets:
        db.session.commit()
    return len(due_tweets)


__all__ = ["publish_due_tweets"]
