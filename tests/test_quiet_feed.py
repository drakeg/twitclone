"""Sprint 12 Story 12.4 relationship-first quiet feed coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Follows, Poll, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts


def _users(app):
    with app.app_context():
        viewer = User(username="quiet_viewer", email="quiet-viewer@example.com", password="hash")
        mutual = User(username="quiet_mutual", email="quiet-mutual@example.com", password="hash")
        one_way = User(username="quiet_oneway", email="quiet-oneway@example.com", password="hash")
        stranger = User(username="quiet_stranger", email="quiet-stranger@example.com", password="hash")
        db.session.add_all([viewer, mutual, one_way, stranger]); db.session.flush()
        db.session.add_all([
            Follows(follower_id=viewer.id, followed_id=mutual.id),
            Follows(follower_id=mutual.id, followed_id=viewer.id),
            Follows(follower_id=viewer.id, followed_id=one_way.id),
        ])
        db.session.commit()
        return viewer.id, mutual.id, one_way.id, stranger.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_quiet_feed_contains_only_self_and_mutual_original_content(app):
    viewer_id, mutual_id, one_way_id, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        db.session.add_all([
            Tweet(content="viewer original", user_id=viewer_id, timestamp=now - timedelta(minutes=4)),
            Tweet(content="mutual original", user_id=mutual_id, timestamp=now - timedelta(minutes=3)),
            Tweet(content="one way original", user_id=one_way_id, timestamp=now - timedelta(minutes=2)),
            Tweet(content="stranger original", user_id=stranger_id, timestamp=now - timedelta(minutes=1)),
            Poll(question="mutual poll", user_id=mutual_id, created_at=now),
        ])
        db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        assert {post["content"] for post in posts} == {"viewer original", "mutual original", "mutual poll"}


def test_quiet_feed_excludes_reposts_and_quotes_even_from_mutuals(app):
    viewer_id, mutual_id, _, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        source = Tweet(content="source", user_id=stranger_id, timestamp=now - timedelta(hours=1))
        db.session.add(source); db.session.flush()
        db.session.add_all([
            Retweet(user_id=mutual_id, tweet_id=source.id, timestamp=now - timedelta(minutes=2)),
            Quote(content="mutual quote", user_id=mutual_id, tweet_id=source.id, timestamp=now - timedelta(minutes=1)),
        ])
        db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        assert not any(post["type"] == "retweet" for post in posts)
        assert not any(post["type"] == "quote" for post in posts)


def test_quiet_mode_ui_explains_rules_and_is_temporary(client, app):
    viewer_id, mutual_id, _, _ = _users(app)
    with app.app_context():
        db.session.add(Tweet(content="mutual visible", user_id=mutual_id)); db.session.commit()
    _login(client, viewer_id)
    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    assert b"Quiet" in response.data
    assert b"accounts where you follow each other" in response.data
    assert b"Reposts and quotes are excluded" in response.data
    assert b"Make Quiet my default" not in response.data


def test_anonymous_quiet_request_falls_back_to_all(client, app):
    _, _, _, stranger_id = _users(app)
    with app.app_context():
        db.session.add(Tweet(content="public stranger", user_id=stranger_id)); db.session.commit()
    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    assert b"public stranger" in response.data
