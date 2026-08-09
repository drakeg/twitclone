"""Timeline ordering and scheduled-visibility tests."""

from datetime import datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Poll, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts


def create_users(app):
    with app.app_context():
        author = User(username="author", email="author@example.com", password="hash")
        actor = User(username="actor", email="actor@example.com", password="hash")
        db.session.add_all([author, actor])
        db.session.commit()
        return author.id, actor.id


def test_scheduled_tweets_become_visible_at_publication_time(app):
    now = datetime(2026, 8, 8, 12, 0, 0)
    author_id, actor_id = create_users(app)
    with app.app_context():
        due = Tweet(
            content="due now",
            user_id=author_id,
            timestamp=now - timedelta(days=1),
            scheduled_at=now,
        )
        future = Tweet(
            content="future hidden",
            user_id=author_id,
            timestamp=now - timedelta(days=1),
            scheduled_at=now + timedelta(minutes=1),
        )
        db.session.add_all([due, future])
        db.session.commit()
        db.session.add_all(
            [
                Retweet(user_id=actor_id, tweet_id=due.id, timestamp=now),
                Quote(
                    user_id=actor_id,
                    tweet_id=due.id,
                    content="due quote",
                    timestamp=now,
                ),
                Retweet(user_id=actor_id, tweet_id=future.id, timestamp=now),
                Quote(
                    user_id=actor_id,
                    tweet_id=future.id,
                    content="future quote hidden",
                    timestamp=now,
                ),
            ]
        )
        db.session.commit()

        posts = build_timeline_posts(now=now)

        contents = [post["content"] for post in posts]
        assert "due now" in contents
        assert "due quote" in contents
        assert "future hidden" not in contents
        assert "future quote hidden" not in contents
        due_post = next(post for post in posts if post["type"] == "tweet")
        assert due_post["timestamp"] == now


def test_future_scheduled_content_appears_after_clock_reaches_schedule(app):
    now = datetime(2026, 8, 8, 12, 0, 0)
    author_id, actor_id = create_users(app)
    with app.app_context():
        scheduled = Tweet(
            content="scheduled original",
            user_id=author_id,
            timestamp=now - timedelta(days=1),
            scheduled_at=now + timedelta(minutes=1),
        )
        db.session.add(scheduled)
        db.session.commit()
        db.session.add_all(
            [
                Retweet(user_id=actor_id, tweet_id=scheduled.id, timestamp=now),
                Quote(
                    user_id=actor_id,
                    tweet_id=scheduled.id,
                    content="scheduled quote",
                    timestamp=now,
                ),
            ]
        )
        db.session.commit()

        before = build_timeline_posts(now=now)
        at_schedule = build_timeline_posts(now=now + timedelta(minutes=1))

        assert before == []
        assert {post["type"] for post in at_schedule} == {"tweet", "retweet", "quote"}
        scheduled_post = next(post for post in at_schedule if post["type"] == "tweet")
        assert scheduled_post["timestamp"] == scheduled.scheduled_at


def test_timeline_exact_ties_use_documented_deterministic_order(app):
    fixed_time = datetime(2026, 8, 8, 12, 0, 0)
    author_id, actor_id = create_users(app)
    with app.app_context():
        original = Tweet(
            content="original",
            user_id=author_id,
            timestamp=fixed_time - timedelta(minutes=1),
        )
        tied_tweet = Tweet(
            content="tied tweet", user_id=author_id, timestamp=fixed_time
        )
        db.session.add_all([original, tied_tweet])
        db.session.commit()
        db.session.add_all(
            [
                Retweet(user_id=actor_id, tweet_id=original.id, timestamp=fixed_time),
                Quote(
                    user_id=actor_id,
                    tweet_id=original.id,
                    content="tied quote",
                    timestamp=fixed_time,
                ),
                Poll(
                    question="tied poll",
                    created_at=fixed_time,
                    duration_days=1,
                    duration_hours=0,
                    duration_minutes=0,
                    user_id=author_id,
                ),
            ]
        )
        db.session.commit()

        tied_posts = [
            post
            for post in build_timeline_posts(now=fixed_time)
            if post["timestamp"] == fixed_time
        ]

        assert [post["type"] for post in tied_posts] == [
            "tweet",
            "retweet",
            "quote",
            "poll",
        ]


def test_same_type_ties_use_higher_source_id_first(app):
    fixed_time = datetime(2026, 8, 8, 12, 0, 0)
    author_id, _ = create_users(app)
    with app.app_context():
        db.session.add_all(
            [
                Tweet(content="first", user_id=author_id, timestamp=fixed_time),
                Tweet(content="second", user_id=author_id, timestamp=fixed_time),
            ]
        )
        db.session.commit()

        posts = build_timeline_posts(now=fixed_time)

        assert [post["content"] for post in posts] == ["second", "first"]
