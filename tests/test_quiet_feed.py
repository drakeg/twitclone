"""Sprint 12 Story 12.4 relationship-first quiet feed coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Follows, Poll, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts


def _users(app):
    with app.app_context():
        viewer = User(username="quiet_viewer", email="quiet-viewer@example.com", password="hash")
        followed = User(username="quiet_followed", email="quiet-followed@example.com", password="hash")
        stranger = User(username="quiet_stranger", email="quiet-stranger@example.com", password="hash")
        db.session.add_all([viewer, followed, stranger])
        db.session.flush()
        db.session.add(Follows(follower_id=viewer.id, followed_id=followed.id))
        db.session.commit()
        return viewer.id, followed.id, stranger.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_quiet_feed_keeps_direct_followed_and_own_content(app):
    viewer_id, followed_id, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        db.session.add_all([
            Tweet(content="viewer direct", user_id=viewer_id, timestamp=now - timedelta(minutes=3)),
            Tweet(content="followed direct", user_id=followed_id, timestamp=now - timedelta(minutes=2)),
            Tweet(content="stranger direct", user_id=stranger_id, timestamp=now - timedelta(minutes=1)),
            Poll(question="followed poll", user_id=followed_id, created_at=now),
        ])
        db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        content = {post["content"] for post in posts}
        assert "viewer direct" in content
        assert "followed direct" in content
        assert "followed poll" in content
        assert "stranger direct" not in content


def test_quiet_feed_removes_reposts_and_quotes_even_from_followed_accounts(app):
    viewer_id, followed_id, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        source = Tweet(content="source", user_id=stranger_id, timestamp=now - timedelta(hours=1))
        db.session.add(source)
        db.session.flush()
        db.session.add_all([
            Retweet(user_id=followed_id, tweet_id=source.id, timestamp=now - timedelta(minutes=2)),
            Quote(content="followed quote", user_id=followed_id, tweet_id=source.id, timestamp=now - timedelta(minutes=1)),
        ])
        db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        assert not any(post["type"] == "retweet" for post in posts)
        assert not any(post["type"] == "quote" for post in posts)


def test_quiet_ui_explains_rules_and_preserves_pagination(client, app):
    viewer_id, followed_id, _ = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        for number in range(22):
            db.session.add(Tweet(content=f"quiet {number}", user_id=followed_id, timestamp=now - timedelta(seconds=number)))
        db.session.commit()
    _login(client, viewer_id)
    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    assert b"Quiet" in response.data
    assert b"Reposts and quote posts are intentionally removed" in response.data
    assert b"No popularity or engagement ranking is applied" in response.data
    assert b"feed=quiet&amp;page=2" in response.data or b"page=2&amp;feed=quiet" in response.data


def test_quiet_mode_is_temporary_and_cannot_be_saved(client, app):
    viewer_id, _, _ = _users(app)
    _login(client, viewer_id)
    response = client.post("/feed-preference", data={"feed_mode": "quiet"})
    assert response.status_code == 400


def test_anonymous_quiet_request_falls_back_to_all(client, app):
    _, _, stranger_id = _users(app)
    with app.app_context():
        db.session.add(Tweet(content="public stranger", user_id=stranger_id))
        db.session.commit()
    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    assert b"public stranger" in response.data
