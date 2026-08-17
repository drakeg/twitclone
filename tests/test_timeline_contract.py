"""Normalized timeline data-contract tests."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Poll, PollOption, PollVote, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts


def seed_timeline(app):
    now = datetime.now(UTC).replace(tzinfo=None)
    with app.app_context():
        author = User(username="author", email="author@example.com", password="hash")
        actor = User(username="actor", email="actor@example.com", password="hash")
        db.session.add_all([author, actor])
        db.session.commit()

        unused = Tweet(
            content="unused", user_id=author.id, timestamp=now - timedelta(minutes=6)
        )
        original = Tweet(
            content="original content",
            user_id=author.id,
            image="original.png",
            timestamp=now - timedelta(minutes=5),
        )
        db.session.add_all([unused, original])
        db.session.commit()

        retweet = Retweet(
            user_id=actor.id,
            tweet_id=original.id,
            timestamp=now - timedelta(minutes=3),
        )
        quote = Quote(
            user_id=actor.id,
            tweet_id=original.id,
            content="quote commentary",
            timestamp=now - timedelta(minutes=2),
        )
        poll = Poll(
            question="poll question",
            created_at=now - timedelta(minutes=1),
            duration_days=1,
            duration_hours=0,
            duration_minutes=0,
            user_id=author.id,
        )
        db.session.add_all([retweet, quote, poll])
        db.session.commit()
        option = PollOption(option_text="yes", poll_id=poll.id)
        db.session.add(option)
        db.session.commit()
        vote = PollVote(poll_id=poll.id, user_id=actor.id, option_id=option.id)
        db.session.add(vote)
        db.session.commit()

        return {
            "now": now,
            "author_id": author.id,
            "actor_id": actor.id,
            "original_id": original.id,
            "retweet_id": retweet.id,
            "quote_id": quote.id,
            "poll_id": poll.id,
        }


def log_in(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_timeline_contract_normalizes_all_content_types(app):
    seeded = seed_timeline(app)
    with app.app_context():
        viewer = db.session.get(User, seeded["actor_id"])
        posts = build_timeline_posts(now=seeded["now"], viewer=viewer)

        assert [post["type"] for post in posts] == [
            "poll",
            "quote",
            "retweet",
            "tweet",
            "tweet",
        ]
        assert [post["timestamp"] for post in posts] == sorted(
            [post["timestamp"] for post in posts], reverse=True
        )

        poll_post, quote_post, retweet_post, original_post, _ = posts
        assert poll_post["poll_id"] == seeded["poll_id"]
        assert poll_post["has_voted"] is True

        assert quote_post["source_id"] == seeded["quote_id"]
        assert quote_post["content"] == "quote commentary"
        assert quote_post["original_tweet"].content == "original content"
        assert quote_post["original_user"].username == "author"
        assert quote_post["action_tweet_id"] == seeded["original_id"]

        assert retweet_post["source_id"] == seeded["retweet_id"]
        assert retweet_post["content"] == "original content"
        assert retweet_post["user"].username == "actor"
        assert retweet_post["original_user"].username == "author"
        assert retweet_post["image"] == "original.png"
        assert retweet_post["action_tweet_id"] == seeded["original_id"]

        assert original_post["content"] == "original content"
        assert original_post["action_tweet_id"] == seeded["original_id"]


def test_timeline_page_renders_retweet_and_quote_context_with_tweet_actions(client, app):
    seeded = seed_timeline(app)
    log_in(client, seeded["actor_id"])

    response = client.get("/")

    assert response.status_code == 200
    assert b"Retweeted from @author" in response.data
    assert b"Quoted @author" in response.data
    assert b"quote commentary" in response.data
    assert response.data.count(b"original content") >= 3
    assert f'/retweet/{seeded["original_id"]}'.encode() in response.data
    assert f'/quote/{seeded["original_id"]}'.encode() in response.data
    assert f'/bookmark/{seeded["original_id"]}'.encode() in response.data


def test_anonymous_poll_contract_does_not_report_a_vote(app):
    seeded = seed_timeline(app)
    with app.app_context():
        posts = build_timeline_posts(now=seeded["now"])

        poll_post = next(post for post in posts if post["type"] == "poll")
        assert poll_post["has_voted"] is False
