from datetime import UTC, datetime, timedelta

from werkzeug.security import generate_password_hash

from twitclone.extensions import db
from twitclone.models import Follows, Poll, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts


def _user(username):
    user = User(username=username, email=f"{username}@example.com", password=generate_password_hash("password"))
    db.session.add(user)
    db.session.flush()
    return user


def test_quiet_feed_keeps_followed_and_own_original_content(app):
    now = datetime.now(UTC).replace(tzinfo=None)
    with app.app_context():
        viewer = _user("viewer")
        followed = _user("followed")
        unrelated = _user("unrelated")
        db.session.add(Follows(follower_id=viewer.id, followed_id=followed.id))
        db.session.add_all([
            Tweet(content="followed original", user_id=followed.id, timestamp=now - timedelta(minutes=3)),
            Tweet(content="own original", user_id=viewer.id, timestamp=now - timedelta(minutes=2)),
            Tweet(content="unrelated original", user_id=unrelated.id, timestamp=now - timedelta(minutes=1)),
            Poll(question="followed poll", user_id=followed.id, created_at=now),
        ])
        db.session.commit()

        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        contents = [post["content"] for post in posts]
        assert "followed original" in contents
        assert "own original" in contents
        assert "followed poll" in contents
        assert "unrelated original" not in contents
        assert {post["type"] for post in posts} <= {"tweet", "poll"}


def test_quiet_feed_omits_reposts_and_quotes_even_from_followed_accounts(app):
    now = datetime.now(UTC).replace(tzinfo=None)
    with app.app_context():
        viewer = _user("viewer2")
        followed = _user("followed2")
        author = _user("author2")
        db.session.add(Follows(follower_id=viewer.id, followed_id=followed.id))
        original = Tweet(content="amplified original", user_id=author.id, timestamp=now - timedelta(minutes=3))
        db.session.add(original)
        db.session.flush()
        db.session.add_all([
            Retweet(user_id=followed.id, tweet_id=original.id, timestamp=now - timedelta(minutes=2)),
            Quote(content="followed quote", user_id=followed.id, tweet_id=original.id, timestamp=now - timedelta(minutes=1)),
        ])
        db.session.commit()

        posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        assert posts == []


def test_quiet_feed_requires_authentication_and_cannot_be_saved(app, client):
    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    assert b"Quiet" not in response.data

    with app.app_context():
        viewer = _user("viewer3")
        db.session.commit()
        viewer_id = viewer.id

    with client.session_transaction() as session:
        session["_user_id"] = str(viewer_id)
        session["_fresh"] = True

    response = client.get("/?feed=quiet")
    assert response.status_code == 200
    response = client.post("/feed-preference", data={"feed_mode": "quiet"})
    assert response.status_code == 400
