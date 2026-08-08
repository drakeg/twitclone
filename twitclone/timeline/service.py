"""Normalized timeline data assembly."""

from twitclone.models import Poll, PollVote, Quote, Retweet, Tweet


def build_timeline_posts(*, now, viewer=None):
    """Return all supported timeline items in newest-first order."""
    posts = []

    visible_tweets = Tweet.query.filter(
        (Tweet.scheduled_at == None) | (Tweet.scheduled_at <= now)
    ).all()
    for tweet in visible_tweets:
        posts.append(
            {
                "id": tweet.id,
                "source_id": tweet.id,
                "action_tweet_id": tweet.id,
                "content": tweet.content,
                "timestamp": tweet.timestamp,
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

    for retweet in Retweet.query.all():
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

    for quote in Quote.query.all():
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

    posts.sort(key=lambda post: post["timestamp"], reverse=True)
    return posts


__all__ = ["build_timeline_posts"]
