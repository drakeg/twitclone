"""Sprint 12 Story 12.1 explicit feed choice coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Follows, Poll, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts


def _users(app):
    with app.app_context():
        viewer = User(username="feed_viewer", email="feed-viewer@example.com", password="hash")
        followed = User(username="feed_followed", email="feed-followed@example.com", password="hash")
        stranger = User(username="feed_stranger", email="feed-stranger@example.com", password="hash")
        db.session.add_all([viewer, followed, stranger]); db.session.flush()
        db.session.add(Follows(follower_id=viewer.id, followed_id=followed.id)); db.session.commit()
        return viewer.id, followed.id, stranger.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id); session["_fresh"] = True


def test_following_feed_contains_followed_and_own_content_only(app):
    viewer_id, followed_id, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        db.session.add_all([
            Tweet(content="viewer post", user_id=viewer_id, timestamp=now - timedelta(minutes=3)),
            Tweet(content="followed post", user_id=followed_id, timestamp=now - timedelta(minutes=2)),
            Tweet(content="stranger post", user_id=stranger_id, timestamp=now - timedelta(minutes=1)),
        ]); db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="following")
        assert {post["content"] for post in posts} == {"viewer post", "followed post"}


def test_following_feed_filters_reposts_quotes_and_polls_by_actor(app):
    viewer_id, followed_id, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        source = Tweet(content="source", user_id=stranger_id, timestamp=now - timedelta(hours=1)); db.session.add(source); db.session.flush()
        db.session.add_all([
            Retweet(user_id=followed_id, tweet_id=source.id, timestamp=now - timedelta(minutes=3)),
            Quote(content="followed quote", user_id=followed_id, tweet_id=source.id, timestamp=now - timedelta(minutes=2)),
            Quote(content="stranger quote", user_id=stranger_id, tweet_id=source.id, timestamp=now - timedelta(minutes=1)),
            Poll(question="followed poll", user_id=followed_id, created_at=now),
        ]); db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="following")
        assert any(post["type"] == "retweet" and post["user"].id == followed_id for post in posts)
        assert any(post["type"] == "quote" and post["content"] == "followed quote" for post in posts)
        assert any(post["type"] == "poll" and post["content"] == "followed poll" for post in posts)
        assert not any(post["type"] == "quote" and post["content"] == "stranger quote" for post in posts)


def test_feed_mode_ui_explains_order_and_preserves_pagination(client, app):
    viewer_id, followed_id, _ = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        for number in range(22):
            db.session.add(Tweet(content=f"followed {number}", user_id=followed_id, timestamp=now - timedelta(seconds=number)))
        db.session.commit()
    _login(client, viewer_id)
    response = client.get("/?feed=following")
    assert response.status_code == 200
    assert b"Following" in response.data
    assert b"No popularity or engagement ranking is applied" in response.data
    assert b"feed=following&amp;page=2" in response.data or b"page=2&amp;feed=following" in response.data


def test_invalid_feed_mode_falls_back_to_all(client, app):
    viewer_id, _, stranger_id = _users(app)
    with app.app_context():
        db.session.add(Tweet(content="public stranger", user_id=stranger_id)); db.session.commit()
    _login(client, viewer_id)
    response = client.get("/?feed=unknown")
    assert response.status_code == 200
    assert b"All Ripple" in response.data
    assert b"public stranger" in response.data
