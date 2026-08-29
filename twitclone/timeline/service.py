"""Normalized timeline data assembly."""

from dataclasses import dataclass
from math import ceil

from twitclone.conversation_intent import conversation_intent_metadata
from twitclone.conversation_models import TweetConversationIntent
from twitclone.models import Poll, PollVote, Quote, Retweet, Tweet
from twitclone.topic_models import public_topic_associations

TIMELINE_TYPE_PRIORITY = {"tweet": 0, "retweet": 1, "quote": 2, "poll": 3}
TIMELINE_PAGE_SIZE = 20
FEED_MODES = {"all", "following", "topic", "quiet"}
PERSISTENT_FEED_MODES = {"all", "following"}


@dataclass(frozen=True)
class TimelinePage:
    items: list
    page: int
    per_page: int
    total_items: int
    total_pages: int

    @property
    def has_previous(self): return self.page > 1
    @property
    def has_next(self): return self.page < self.total_pages
    @property
    def previous_page(self): return self.page - 1 if self.has_previous else None
    @property
    def next_page(self): return self.page + 1 if self.has_next else None


def _visible_tweet_filter(now):
    return ((Tweet.scheduled_at == None) | (Tweet.scheduled_at <= now)) & (Tweet.is_removed.is_(False))


def _tweet_timeline_timestamp(tweet):
    return tweet.scheduled_at if tweet.scheduled_at is not None else tweet.timestamp


def _tweet_conversation_intent(tweet):
    record = TweetConversationIntent.query.filter_by(tweet_id=tweet.id).first()
    return conversation_intent_metadata(record.intent if record else None)


def _tweet_conversation_state(tweet):
    record = getattr(tweet, "conversation_state_record", None)
    return {"is_closed": bool(record and record.is_closed), "is_resolved": bool(record and record.is_resolved)}


def _tweet_topics(tweet):
    return [{"name": association.topic.name, "slug": association.topic.slug, "source": association.source} for association in public_topic_associations(tweet)]


def _has_explicit_topic(tweet, topic_slug):
    if not topic_slug:
        return False
    return any(topic["slug"] == topic_slug and topic["source"] == "explicit" for topic in _tweet_topics(tweet))


def _following_ids(viewer):
    if viewer is None or not viewer.is_authenticated:
        return None
    return {user.id for user in viewer.followed.all()} | {viewer.id}


def _quiet_ids(viewer):
    if viewer is None or not viewer.is_authenticated:
        return None
    followed_ids = {user.id for user in viewer.followed.all()}
    follower_ids = {user.id for user in viewer.followers.all()}
    return (followed_ids & follower_ids) | {viewer.id}


def build_timeline_posts(*, now, viewer=None, feed_mode="all", topic_slug=None):
    if feed_mode not in FEED_MODES:
        feed_mode = "all"
    if feed_mode == "following":
        allowed_user_ids = _following_ids(viewer)
    elif feed_mode == "quiet":
        allowed_user_ids = _quiet_ids(viewer)
    else:
        allowed_user_ids = None
    if feed_mode in {"following", "quiet"} and allowed_user_ids is None:
        feed_mode = "all"
    if feed_mode == "topic" and not topic_slug:
        feed_mode = "all"

    def include_user(user_id):
        return allowed_user_ids is None or user_id in allowed_user_ids

    def include_tweet(tweet):
        return feed_mode != "topic" or _has_explicit_topic(tweet, topic_slug)

    posts = []
    for tweet in Tweet.query.filter(_visible_tweet_filter(now)).all():
        if include_user(tweet.user_id) and include_tweet(tweet):
            posts.append({"id": tweet.id, "source_id": tweet.id, "action_tweet_id": tweet.id, "content": tweet.content, "timestamp": _tweet_timeline_timestamp(tweet), "type": "tweet", "user": tweet.user, "image": tweet.image, "original_tweet": None, "original_user": None, "poll": None, "poll_id": None, "has_voted": False, "report_type": "tweet", "report_id": tweet.id, "report_author_id": tweet.user_id, "conversation_intent": _tweet_conversation_intent(tweet), "conversation_state": _tweet_conversation_state(tweet), "topics": _tweet_topics(tweet)})
    if feed_mode != "quiet":
        for retweet in Retweet.query.join(Retweet.tweet).filter(_visible_tweet_filter(now)).all():
            if include_user(retweet.user_id) and include_tweet(retweet.tweet):
                posts.append({"id": retweet.id, "source_id": retweet.id, "action_tweet_id": retweet.tweet_id, "content": retweet.tweet.content, "timestamp": retweet.timestamp, "type": "retweet", "user": retweet.user, "image": retweet.tweet.image, "original_tweet": retweet.tweet, "original_user": retweet.tweet.user, "poll": None, "poll_id": None, "has_voted": False, "report_type": "tweet", "report_id": retweet.tweet_id, "report_author_id": retweet.tweet.user_id, "conversation_intent": _tweet_conversation_intent(retweet.tweet), "conversation_state": _tweet_conversation_state(retweet.tweet), "topics": _tweet_topics(retweet.tweet)})
    if feed_mode != "topic":
        for quote in Quote.query.join(Quote.tweet).filter(_visible_tweet_filter(now), Quote.is_removed.is_(False)).all():
            if include_user(quote.user_id):
                posts.append({"id": quote.id, "source_id": quote.id, "action_tweet_id": quote.tweet_id, "content": quote.content, "timestamp": quote.timestamp, "type": "quote", "user": quote.user, "image": None, "original_tweet": quote.tweet, "original_user": quote.tweet.user, "poll": None, "poll_id": None, "has_voted": False, "report_type": "quote", "report_id": quote.id, "report_author_id": quote.user_id, "conversation_intent": None, "conversation_state": None, "topics": []})
        for poll in Poll.query.filter_by(is_removed=False).all():
            if not include_user(poll.user_id):
                continue
            has_voted = False
            if viewer is not None and viewer.is_authenticated:
                has_voted = PollVote.query.filter_by(poll_id=poll.id, user_id=viewer.id).first() is not None
            posts.append({"id": poll.id, "source_id": poll.id, "action_tweet_id": None, "content": poll.question, "timestamp": poll.created_at, "type": "poll", "user": poll.user, "image": None, "original_tweet": None, "original_user": None, "poll": poll, "poll_id": poll.id, "has_voted": has_voted, "poll_is_active": poll.is_active_at(now), "report_type": "poll", "report_id": poll.id, "report_author_id": poll.user_id, "conversation_intent": None, "conversation_state": None, "topics": []})
    posts.sort(key=lambda post: (post["timestamp"], -TIMELINE_TYPE_PRIORITY[post["type"]], post["source_id"]), reverse=True)
    return posts


def paginate_timeline_posts(posts, *, page, per_page=TIMELINE_PAGE_SIZE):
    if per_page < 1: raise ValueError("per_page must be at least 1")
    total_items = len(posts); total_pages = max(1, ceil(total_items / per_page)); bounded_page = min(max(page, 1), total_pages)
    start = (bounded_page - 1) * per_page; end = start + per_page
    return TimelinePage(items=posts[start:end], page=bounded_page, per_page=per_page, total_items=total_items, total_pages=total_pages)


__all__ = ["FEED_MODES", "PERSISTENT_FEED_MODES", "TIMELINE_PAGE_SIZE", "TIMELINE_TYPE_PRIORITY", "TimelinePage", "build_timeline_posts", "paginate_timeline_posts"]
