"""Sprint 12 Story 12.4 relationship-first Quiet feed coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Follows, Poll, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts


def _users(app):
    with app.app_context():
        viewer = User(username="quiet_viewer", email="quiet-viewer@example.com", password="hash")
        mutual = User(username="quiet_mutual", email="quiet-mutual@example.com", password="hash")
        one_way = User(username="quiet_one_way", email="quiet-one-way@example.com", password="hash")
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


def test_quiet_feed_contains_only_self_and_mutual_direct_activity(app):
    viewer_id, mutual_id, one_way_id, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        source = Tweet(content="source", user_id=stranger_id, timestamp=now - timedelta(hours=1))
        db.session.add(source); db.session.flush()
        db.session.add_all([
            Tweet(content="viewer direct", user_id=viewer_id, timestamp=now - timedelta(minutes=5)),
            Tweet(content="mutual direct", user_id=mutual_id, timestamp=now - timedelta(minutes=4)),
            Tweet(content="one way direct", user_id=one_way_id, timestamp=now - timedelta(minutes=3)),
            Tweet(content="stranger direct", user_id=stranger_id, timestamp=now - timedelta(minutes=2)),
            Quote(content="mutual quote", user_id=mutual_id, tweet_id=source.id, timestamp=now - timedelta(minutes=1)),
            Quote(content="one way quote", user_id=one_way_id, tweet_id=source.id, timestamp=now),
            Poll(question="mutual poll", user_id=mutual_id, created_at=now, duration_days=1, duration_hours=0, duration_minutes=0),
            Poll(question="one way poll", user_id=one_way_id, created_at=now, duration_days=1, duration_hours=0, duration_minutes=0),
        ])
        db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        contents = {post["content"] for post in posts}
        assert "viewer direct" in contents
        assert "mutual direct" in contents
        assert "mutual quote" in contents
        assert "mutual poll" in contents
        assert "one way direct" not in contents
        assert "one way quote" not in contents
        assert "one way poll" not in contents
        assert "stranger direct" not in contents


def test_quiet_feed_excludes_reposts_even_from_mutual_connections(app):
    viewer_id, mutual_id, _, stranger_id = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        source = Tweet(content="amplified source", user_id=stranger_id, timestamp=now - timedelta(hours=1))
        db.session.add(source); db.session.flush()
        db.session.add(Retweet(user_id=mutual_id, tweet_id=source.id, timestamp=now))
        db.session.commit()
        viewer = db.session.get(User, viewer_id)
        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        assert not any(post["type"] == "retweet" for post in posts)


def test_quiet_feed_ui_explains_relationship_and_pagination(client, app):
    viewer_id, mutual_id, _, _ = _users(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        for number in range(22):
            db.session.add(Tweet(content=f"mutual quiet {number}", user_id=mutual_id, timestamp=now - timedelta(seconds=number)))
        db.session.commit()
    _login(client, viewer_id)
    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    assert b"mutual connections" in response.data
    assert b"Reposts are excluded" in response.data
    assert b"No popularity or engagement ranking is applied" in response.data
    assert b"feed=quiet&amp;page=2" in response.data or b"page=2&amp;feed=quiet" in response.data


def test_quiet_feed_cannot_be_persisted(client, app):
    viewer_id, _, _, _ = _users(app)
    _login(client, viewer_id)
    response = client.post("/feed-preference", data={"feed_mode": "quiet"})
    assert response.status_code == 400


def test_anonymous_quiet_request_falls_back_to_all(client, app):
    _, _, _, stranger_id = _users(app)
    with app.app_context():
        db.session.add(Tweet(content="anonymous public", user_id=stranger_id)); db.session.commit()
    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    assert b"anonymous public" in response.data
    assert b'aria-label="Feed mode"' not in response.data
