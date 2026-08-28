"""Transparent topic contributor discovery for Sprint 10 Story 10.4."""

from twitclone.models import Tweet, User
from twitclone.topic_models import Topic, TweetTopic
from twitclone.topic_reputation import topic_reputation_summary

LEVEL_PRIORITY = {
    "Established contributor": 3,
    "Recognized contributor": 2,
    "Emerging contributor": 1,
    "Building contribution history": 0,
    "No contribution history yet": -1,
}


def topic_contributors(topic_slug):
    """Return contributors for one topic using an explicit, inspectable ordering rule.

    Qualification requires at least one non-removed post where the author explicitly
    selected the topic. Ordering uses the visible reputation level first, followed by
    visible evidence dimensions, then username for deterministic ties. Followers,
    impressions, paid plans, and verification are not part of qualification or order.
    """
    topic = Topic.query.filter_by(slug=topic_slug).first()
    if topic is None:
        return None, []

    user_ids = (
        User.query.with_entities(User.id)
        .join(Tweet, Tweet.user_id == User.id)
        .join(TweetTopic, TweetTopic.tweet_id == Tweet.id)
        .filter(
            TweetTopic.topic_id == topic.id,
            TweetTopic.source == "explicit",
            Tweet.is_removed.is_(False),
        )
        .distinct()
        .all()
    )

    contributors = []
    for (user_id,) in user_ids:
        user = User.query.get(user_id)
        summary = topic_reputation_summary(user_id, topic.slug)
        if user is None or summary is None:
            continue
        contributors.append({"user": user, "summary": summary})

    contributors.sort(
        key=lambda item: (
            -LEVEL_PRIORITY.get(item["summary"]["level"], -1),
            -item["summary"]["evidence"]["unique_recognizers"],
            -item["summary"]["evidence"]["recognized_posts"],
            -item["summary"]["evidence"]["total_constructive_signals"],
            item["user"].username.casefold(),
        )
    )
    return topic, contributors


__all__ = ["LEVEL_PRIORITY", "topic_contributors"]
