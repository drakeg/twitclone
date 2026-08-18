"""Username mention extraction and notification helpers."""

import re

from twitclone.extensions import db
from twitclone.models import Notification, User

MENTION_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_]+)")


def mentioned_usernames(content: str) -> set[str]:
    return {match.group(1).lower() for match in MENTION_RE.finditer(content or "")}


def add_mention_notifications(*, content: str, author: User, tweet_id: int) -> int:
    """Queue one notification per valid mentioned user, excluding the author."""
    usernames = mentioned_usernames(content)
    if not usernames:
        return 0

    users = User.query.filter(db.func.lower(User.username).in_(usernames)).all()
    recipients = [user for user in users if user.id != author.id]
    for user in recipients:
        db.session.add(
            Notification(
                user_id=user.id,
                message=f"{author.username} mentioned you in a post",
                tweet_id=tweet_id,
            )
        )
    return len(recipients)


__all__ = ["add_mention_notifications", "mentioned_usernames"]
