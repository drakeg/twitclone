"""Normalized timeline data assembly."""

from dataclasses import dataclass
from math import ceil

from twitclone.models import Poll, PollVote, Quote, Retweet, Tweet

TIMELINE_TYPE_PRIORITY = {"tweet": 0, "retweet": 1, "quote": 2, "poll": 3}
TIMELINE_PAGE_SIZE = 20


@dataclass(frozen=True)
class TimelinePage:
    items: list
    page: int
    per_page: int
    total_items: int
    total_pages: int

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.total_pages

    @property
    def previous_page(self):
        return self.page - 1 if self.has_previous else None

    @property
    def next_page(self):
        return self.page + 1 if self.has_next else None


def _visible_tweet_filter(now):
    return (Tweet.scheduled_at == None) | (Tweet.scheduled_at <= now)


def _tweet_timeline_timestamp(tweet):
    return tweet.scheduled_at if tweet.scheduled_at is not None else tweet.timestamp


def build_timeline_posts(*, now, viewer=None):
    """Return all supported timeline items in newest-first order."""
    posts = []

    visible_tweets = Tweet.query.filter(_visible_tweet_filter(now)).all()
    for tweet in visible_tweets:
        posts.append(
            {
                "id": tweet.id,
                "source_id": tweet.id,
                "action_tweet_id": tweet.id,
                "content": tweet.content,
                "timestamp": _tweet_timeline_timestamp(tweet),
                "type": "tweet",
                "user": tweet.user,
                "image": tweet.image,
                "original_tweet": None,
                "original_user": None,
                "poll": None,
                "poll_id": None,
                "has_voted": False,
            }
        )

    visible_retweets = (
        Retweet.query.join(Retweet.tweet).filter(_visible_tweet_filter(now)).all()
    )
    for retweet in visible_retweets:
        posts.append(
            {
                "id": retweet.id,
                "source_id": retweet.id,
                "action_tweet_id": retweet.tweet_id,
                "content": retweet.tweet.content,
                "timestamp": retweet.timestamp,
                "type": "retweet",
                "user": retweet.user,
                "image": retweet.tweet.image,
                "original_tweet": retweet.tweet,
                "original_user": retweet.tweet.user,
                "poll": None,
                "poll_id": None,
                "has_voted": False,
            }
        )

    visible_quotes = Quote.query.join(Quote.tweet).filter(_visible_tweet_filter(now)).all()
    for quote in visible_quotes:
        posts.append(
            {
                "id": quote.id,
                "source_id": quote.id,
                "action_tweet_id": quote.tweet_id,
                "content": quote.content,
                "timestamp": quote.timestamp,
                "type": "quote",
                "user": quote.user,
                "image": None,
                "original_tweet": quote.tweet,
                "original_user": quote.tweet.user,
                "poll": None,
                "poll_id": None,
                "has_voted": False,
            }
        )

    for poll in Poll.query.all():
        has_voted = False
        if viewer is not None and viewer.is_authenticated:
            has_voted = (
                PollVote.query.filter_by(poll_id=poll.id, user_id=viewer.id).first()
                is not None
            )
        posts.append(
            {
                "id": poll.id,
                "source_id": poll.id,
                "action_tweet_id": None,
                "content": poll.question,
                "timestamp": poll.created_at,
                "type": "poll",
                "user": poll.user,
                "image": None,
                "original_tweet": None,
                "original_user": None,
                "poll": poll,
                "poll_id": poll.id,
                "has_voted": has_voted,
            }
        )

    posts.sort(
        key=lambda post: (
            post["timestamp"],
            -TIMELINE_TYPE_PRIORITY[post["type"]],
            post["source_id"],
        ),
        reverse=True,
    )
    return posts


def paginate_timeline_posts(posts, *, page, per_page=TIMELINE_PAGE_SIZE):
    """Return one bounded page from an already ordered timeline."""
    if per_page < 1:
        raise ValueError("per_page must be at least 1")

    total_items = len(posts)
    total_pages = max(1, ceil(total_items / per_page))
    bounded_page = min(max(page, 1), total_pages)
    start = (bounded_page - 1) * per_page
    end = start + per_page
    return TimelinePage(
        items=posts[start:end],
        page=bounded_page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
    )


__all__ = [
    "TIMELINE_PAGE_SIZE",
    "TIMELINE_TYPE_PRIORITY",
    "TimelinePage",
    "build_timeline_posts",
    "paginate_timeline_posts",
]
