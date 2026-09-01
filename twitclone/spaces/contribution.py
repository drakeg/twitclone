"""Derived, space-local constructive contribution context.

This module intentionally computes context from existing public/space records instead
of persisting a mutable community reputation score.
"""

from collections import defaultdict

from twitclone.contribution_models import ConstructiveContribution
from twitclone.models import Tweet, User
from twitclone.spaces.models import SpaceMembership, SpacePost

SIGNAL_LABELS = {
    "helpful": "Helpful",
    "thoughtful": "Thoughtful",
    "context": "Useful context",
}


def build_space_contribution_context(space):
    """Return explainable contribution context for current members of ``space``.

    Eligible evidence is deliberately narrow:
    - the recognized post must be visible and scoped to this space;
    - the post author must still be a current member;
    - the recognizer must still be a current member;
    - self-recognition never counts.

    Results are alphabetical rather than score-ranked. This context does not affect
    global reputation, feed ordering, moderation authority, verification, or paid
    entitlement.
    """
    member_rows = SpaceMembership.query.filter_by(space_id=space.id).all()
    member_ids = {row.user_id for row in member_rows}
    if not member_ids:
        return {"members": [], "signal_total": 0, "recognized_posts": 0, "unique_recognizers": 0}

    visible_rows = (
        SpacePost.query.join(SpacePost.tweet)
        .filter(
            SpacePost.space_id == space.id,
            SpacePost.is_hidden.is_(False),
            Tweet.is_removed.is_(False),
            Tweet.user_id.in_(member_ids),
        )
        .all()
    )
    tweet_author = {row.tweet_id: row.tweet.user_id for row in visible_rows}
    if not tweet_author:
        return {"members": [], "signal_total": 0, "recognized_posts": 0, "unique_recognizers": 0}

    signals = ConstructiveContribution.query.filter(
        ConstructiveContribution.tweet_id.in_(tweet_author),
        ConstructiveContribution.user_id.in_(member_ids),
    ).all()

    by_author = defaultdict(lambda: {
        "signal_counts": {key: 0 for key in SIGNAL_LABELS},
        "recognized_post_ids": set(),
        "recognizer_ids": set(),
    })
    all_recognizers = set()
    all_posts = set()
    signal_total = 0

    for signal in signals:
        author_id = tweet_author.get(signal.tweet_id)
        if author_id is None or signal.user_id == author_id:
            continue
        summary = by_author[author_id]
        summary["signal_counts"][signal.signal] += 1
        summary["recognized_post_ids"].add(signal.tweet_id)
        summary["recognizer_ids"].add(signal.user_id)
        all_recognizers.add(signal.user_id)
        all_posts.add(signal.tweet_id)
        signal_total += 1

    users = {
        user.id: user
        for user in User.query.filter(User.id.in_(by_author.keys())).all()
    } if by_author else {}
    members = []
    for author_id, summary in by_author.items():
        user = users.get(author_id)
        if user is None:
            continue
        members.append({
            "user": user,
            "signal_counts": summary["signal_counts"],
            "signal_total": sum(summary["signal_counts"].values()),
            "recognized_posts": len(summary["recognized_post_ids"]),
            "unique_recognizers": len(summary["recognizer_ids"]),
        })
    members.sort(key=lambda item: item["user"].username.casefold())

    return {
        "members": members,
        "signal_total": signal_total,
        "recognized_posts": len(all_posts),
        "unique_recognizers": len(all_recognizers),
    }


__all__ = ["SIGNAL_LABELS", "build_space_contribution_context"]
