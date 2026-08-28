"""Explainable topic reputation summaries for Sprint 10 Story 10.3."""

from twitclone.topic_evidence import topic_contribution_evidence
from twitclone.topic_models import Topic, TweetTopic


LEVELS = (
    ("Established contributor", 5, 3, 3),
    ("Recognized contributor", 3, 2, 2),
    ("Emerging contributor", 1, 1, 1),
)


def topic_reputation_level(evidence):
    """Return a plain-language level from transparent evidence thresholds."""
    if evidence is None:
        return None
    for label, minimum_signals, minimum_posts, minimum_recognizers in LEVELS:
        if (
            evidence["total_constructive_signals"] >= minimum_signals
            and evidence["recognized_posts"] >= minimum_posts
            and evidence["unique_recognizers"] >= minimum_recognizers
        ):
            return label
    if evidence["eligible_posts"]:
        return "Building contribution history"
    return "No contribution history yet"


def topic_reputation_summary(user_id, topic_slug):
    """Return one explainable topic summary for a contributor."""
    evidence = topic_contribution_evidence(user_id, topic_slug)
    if evidence is None:
        return None
    return {
        "topic": evidence["topic"],
        "level": topic_reputation_level(evidence),
        "evidence": evidence,
        "explanation": (
            "Based only on constructive recognition on posts where this topic was explicitly selected. "
            "Followers, impressions, paid plans, and verification do not affect this summary."
        ),
    }


def topic_reputation_summaries(user_id):
    """Return summaries for topics the user explicitly associated with eligible posts."""
    topics = (
        Topic.query.join(TweetTopic, TweetTopic.topic_id == Topic.id)
        .filter(TweetTopic.source == "explicit")
        .join(TweetTopic.tweet)
        .filter_by(user_id=user_id, is_removed=False)
        .distinct()
        .order_by(Topic.name.asc())
        .all()
    )
    return [topic_reputation_summary(user_id, topic.slug) for topic in topics]


__all__ = [
    "LEVELS",
    "topic_reputation_level",
    "topic_reputation_summary",
    "topic_reputation_summaries",
]
