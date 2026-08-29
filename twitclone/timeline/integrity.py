"""Explicit feed integrity boundaries for Ripple.

This module is deliberately declarative. Feed assembly lives in ``service.py``;
these constants document and test the product contract that must remain true as
new discovery modes are added.
"""

ORDERING_RULE = "newest-first"

FEED_MODE_RULES = {
    "all": "all visible content",
    "following": "viewer and explicitly followed accounts",
    "topic": "author-selected explicit topic associations",
    "quiet": "viewer and reciprocal follows, without repost amplification",
}

ALLOWED_INCLUSION_INPUTS = frozenset(
    {
        "content visibility",
        "authored/acted-by account",
        "explicit follow relationship",
        "reciprocal follow relationship",
        "author-selected explicit topic",
        "content type",
        "timestamp",
    }
)

FORBIDDEN_RANKING_INPUTS = frozenset(
    {
        "likes or constructive-signal totals",
        "repost totals",
        "reply or quote totals",
        "impression totals",
        "profile-visit totals",
        "follower count",
        "verification status",
        "paid subscription or entitlement",
        "engagement velocity",
        "inferred emotional state",
        "inferred political ideology",
        "inferred sensitive interest",
    }
)

MEASUREMENT_POLICY = {
    "existing_post_impressions": "allowed for aggregate/creator reporting after feed selection",
    "profile_visits": "allowed for aggregate/creator reporting, not feed ordering",
    "follower_snapshots": "allowed for aggregate/creator reporting, not feed ordering",
    "feed_choice_history": "not collected by Sprint 12",
    "topic_query_history": "not collected by Sprint 12",
}

__all__ = [
    "ALLOWED_INCLUSION_INPUTS",
    "FEED_MODE_RULES",
    "FORBIDDEN_RANKING_INPUTS",
    "MEASUREMENT_POLICY",
    "ORDERING_RULE",
]
