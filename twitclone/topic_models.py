"""Explicit topic vocabulary and post associations for Sprint 10."""

import re
from datetime import UTC, datetime

from twitclone.extensions import db

_TOPIC_SPACE_RE = re.compile(r"\s+")
_TOPIC_SLUG_RE = re.compile(r"[^a-z0-9]+")
_HASHTAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_]{1,50})")
MAX_TOPIC_NAME_LENGTH = 80
MAX_TOPICS_PER_POST = 5


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def normalize_topic_name(value):
    """Return a compact display name or None for an unusable topic label."""
    if value is None:
        return None
    name = _TOPIC_SPACE_RE.sub(" ", str(value).strip().lstrip("#")).strip()
    if not name:
        return None
    return name[:MAX_TOPIC_NAME_LENGTH]


def topic_slug(value):
    name = normalize_topic_name(value)
    if not name:
        return None
    slug = _TOPIC_SLUG_RE.sub("-", name.casefold()).strip("-")
    return slug or None


def explicit_topic_values(raw_value):
    """Normalize comma-separated composer topics, preserving first-seen order."""
    values = []
    seen = set()
    for raw in (raw_value or "").split(","):
        name = normalize_topic_name(raw)
        slug = topic_slug(name)
        if not name or not slug or slug in seen:
            continue
        seen.add(slug)
        values.append((name, slug))
        if len(values) >= MAX_TOPICS_PER_POST:
            break
    return values


def hashtag_topic_values(content):
    """Extract deterministic hashtag-derived topic candidates from public post text."""
    values = []
    seen = set()
    for match in _HASHTAG_RE.finditer(content or ""):
        raw = match.group(1).replace("_", " ")
        name = normalize_topic_name(raw)
        slug = topic_slug(name)
        if not name or not slug or slug in seen:
            continue
        seen.add(slug)
        values.append((name, slug))
        if len(values) >= MAX_TOPICS_PER_POST:
            break
    return values


class Topic(db.Model):
    __tablename__ = "topic"
    __table_args__ = (db.UniqueConstraint("slug", name="uq_topic_slug"),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(MAX_TOPIC_NAME_LENGTH), nullable=False)
    slug = db.Column(db.String(MAX_TOPIC_NAME_LENGTH), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)


class TweetTopic(db.Model):
    __tablename__ = "tweet_topic"
    __table_args__ = (
        db.UniqueConstraint("tweet_id", "topic_id", name="uq_tweet_topic_tweet_topic"),
        db.CheckConstraint("source in ('explicit', 'hashtag')", name="ck_tweet_topic_source"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)
    source = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    tweet = db.relationship(
        "Tweet",
        backref=db.backref("topic_associations", lazy=True, cascade="all, delete-orphan"),
    )
    topic = db.relationship("Topic", backref=db.backref("tweet_associations", lazy=True))


def associate_topics(tweet, *, explicit_raw=None, content=None):
    """Attach explicit and hashtag-derived topics without treating hashtags as authoritative expertise."""
    candidates = [(name, slug, "explicit") for name, slug in explicit_topic_values(explicit_raw)]
    candidates.extend((name, slug, "hashtag") for name, slug in hashtag_topic_values(content))

    seen = set()
    for name, slug, source in candidates:
        if slug in seen:
            continue
        seen.add(slug)
        topic = Topic.query.filter_by(slug=slug).first()
        if topic is None:
            topic = Topic(name=name, slug=slug)
            db.session.add(topic)
            db.session.flush()
        db.session.add(TweetTopic(tweet_id=tweet.id, topic_id=topic.id, source=source))


def public_topic_associations(tweet):
    """Return topic associations only for eligible public posts."""
    if tweet.is_removed:
        return []
    return list(tweet.topic_associations)


__all__ = [
    "MAX_TOPICS_PER_POST",
    "Topic",
    "TweetTopic",
    "associate_topics",
    "explicit_topic_values",
    "hashtag_topic_values",
    "normalize_topic_name",
    "public_topic_associations",
    "topic_slug",
]
