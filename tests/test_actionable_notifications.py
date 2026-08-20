"""Regression coverage for post-linked activity notifications."""

from twitclone.extensions import db
from twitclone.models import Notification, Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _users(app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        db.session.add_all([alice, bob])
        db.session.commit()
        return alice.id, bob.id


def test_mention_notification_links_to_exact_post(client, app):
    alice_id, bob_id = _users(app)
    _login(client, alice_id)
    client.post("/tweet", data={"content": "This is the exact @bob mention."})

    with app.app_context():
        tweet = Tweet.query.filter_by(content="This is the exact @bob mention.").one()
        notice = Notification.query.filter_by(user_id=bob_id).one()
        assert notice.tweet_id == tweet.id
        tweet_id = tweet.id

    _login(client, bob_id)
    notifications = client.get("/notifications")
    assert f'/post/{tweet_id}'.encode() in notifications.data
    assert b"This is the exact @bob mention." in notifications.data

    detail = client.get(f"/post/{tweet_id}")
    assert detail.status_code == 200
    assert b"This is the exact " in detail.data
    assert b'href="/profile/bob">@bob</a> mention.' in detail.data


def test_repost_notification_links_to_original_post(client, app):
    alice_id, bob_id = _users(app)
    with app.app_context():
        tweet = Tweet(content="The post that gets reposted.", user_id=alice_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    _login(client, bob_id)
    client.post(f"/retweet/{tweet_id}")

    with app.app_context():
        notice = Notification.query.filter_by(user_id=alice_id).one()
        assert notice.tweet_id == tweet_id

    _login(client, alice_id)
    notifications = client.get("/notifications")
    assert f'/post/{tweet_id}'.encode() in notifications.data
    assert b"The post that gets reposted." in notifications.data
