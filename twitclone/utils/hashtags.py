"""Timeline discovery helpers backed by package-owned models."""

from __future__ import annotations

import re

from twitclone.models import Tweet, User


def get_newest_users(limit: int = 5):
    """Return the newest users using the existing descending-id ordering."""
    return User.query.order_by(User.id.desc()).limit(limit).all()


def get_trending_hashtags(limit: int = 5) -> list[str]:
    """Return hashtag names ordered by descending occurrence count."""
    hashtags: dict[str, int] = {}
    for tweet in Tweet.query.filter_by(is_removed=False).all():
        for tag in re.findall(r"#(\w+)", tweet.content):
            hashtags[tag] = hashtags.get(tag, 0) + 1

    sorted_hashtags = sorted(hashtags.items(), key=lambda item: item[1], reverse=True)
    return [tag for tag, _count in sorted_hashtags[:limit]]
