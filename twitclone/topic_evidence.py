"""Derived, explainable topic contribution evidence for Sprint 10 Story 10.2."""

from collections import Counter

from twitclone.contribution_models import ConstructiveContribution
from twitclone.models import Tweet
from twitclone.topic_models import Topic, TweetTopic

SIGNAL_LABELS = {
    "helpful": "Helpful",
    "thoughtful": "Thoughtful",
    "context": "Useful context",
}


def topic_contribution_evidence(user_id, topic_slug):
    """Return reproducible contribution evidence for one author/topic pair.

    Evidence is intentionally derived rather than persisted as a mutable score.
    Only explicitly selected topics qualify. Hashtag-only associations remain
    discovery metadata and do not become expertise evidence by themselves.
    """
    topic = Topic.query.filter_by(slug=topic_slug).first()
    if topic is None:
        return None

    eligible_tweets = (
        Tweet.query.join(TweetTopic, TweetTopic.tweet_id == Tweet.id)
        .filter(
            Tweet.user_id == user_id,
            Tweet.is_removed.is_(False),
            TweetTopic.topic_id == topic.id,
            TweetTopic.source == "explicit",
        )
        .all()
    )
    tweet_ids = [tweet.id for tweet in eligible_tweets]

    if tweet_ids:
        rows = ConstructiveContribution.query.filter(
            ConstructiveContribution.tweet_id.in_(tweet_ids),
            ConstructiveContribution.user_id != user_id,
        ).all()
    else:
        rows = []

    signal_counts = Counter(row.signal for row in rows if row.signal in SIGNAL_LABELS)
    recognizer_ids = {row.user_id for row in rows if row.signal in SIGNAL_LABELS}
    recognized_post_ids = {row.tweet_id for row in rows if row.signal in SIGNAL_LABELS}

    return {
        "topic": topic,
        "eligible_posts": len(eligible_tweets),
        "recognized_posts": len(recognized_post_ids),
        "unique_recognizers": len(recognizer_ids),
        "signals": {
            key: {"label": label, "count": signal_counts.get(key, 0)}
            for key, label in SIGNAL_LABELS.items()
        },
        "total_constructive_signals": sum(signal_counts.values()),
        "rules": {
            "explicit_topics_only": True,
            "removed_posts_excluded": True,
            "self_signals_excluded": True,
            "followers_excluded": True,
            "impressions_excluded": True,
            "paid_status_excluded": True,
        },
    }


__all__ = ["SIGNAL_LABELS", "topic_contribution_evidence"]
