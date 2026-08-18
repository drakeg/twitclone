"""Regression coverage for mentions and followed hashtags."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import HashtagFollow, Notification, Tweet, User
from twitclone.scheduling import publish_due_tweets


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _users(app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        carol = User(username="Carol_1", email="carol@example.com", password="hash")
        db.session.add_all([alice, bob, carol])
        db.session.commit()
        return alice.id, bob.id, carol.id


def test_post_mentions_notify_each_valid_user_once(client, app):
    alice_id, bob_id, carol_id = _users(app)
    _login(client, alice_id)

    response = client.post(
        "/tweet",
        data={"content": "Hello @bob and @Carol_1 — also @bob again and @missing."},
    )

    assert response.status_code == 302
    with app.app_context():
        bob_notices = Notification.query.filter_by(user_id=bob_id).all()
        carol_notices = Notification.query.filter_by(user_id=carol_id).all()
        assert [item.message for item in bob_notices] == ["alice mentioned you in a post"]
        assert [item.message for item in carol_notices] == ["alice mentioned you in a post"]
        assert Notification.query.filter_by(user_id=alice_id).count() == 0


def test_scheduled_post_mentions_notify_when_published_not_when_scheduled(client, app):
    alice_id, bob_id, _ = _users(app)
    _login(client, alice_id)
    future = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)

    client.post(
        "/tweet",
        data={
            "content": "Later hello @bob",
            "scheduled_date": future.strftime("%Y-%m-%d"),
            "scheduled_time": future.strftime("%H:%M"),
        },
    )
    with app.app_context():
        assert Notification.query.filter_by(user_id=bob_id).count() == 0
        tweet = Tweet.query.filter_by(content="Later hello @bob").one()
        publish_at = tweet.scheduled_at
        assert publish_due_tweets(now=publish_at) == 1
        assert Notification.query.filter_by(user_id=bob_id).count() == 1


def test_hashtag_can_be_followed_once_and_unfollowed(client, app):
    alice_id, _, _ = _users(app)
    _login(client, alice_id)

    first = client.post("/hashtag/Python/follow")
    second = client.post("/hashtag/python/follow")
    assert first.status_code == 302
    assert second.status_code == 302
    with app.app_context():
        follows = HashtagFollow.query.filter_by(user_id=alice_id).all()
        assert len(follows) == 1
        assert follows[0].hashtag == "python"

    page = client.get("/hashtag/python")
    assert b"Following" in page.data
    assert b"Your topics" in page.data
    assert b"#python" in page.data

    response = client.post("/hashtag/python/unfollow")
    assert response.status_code == 302
    with app.app_context():
        assert HashtagFollow.query.filter_by(user_id=alice_id).count() == 0
