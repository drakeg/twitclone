"""End-to-end regression coverage for Sprint 4 social interactions."""

from twitclone.extensions import db
from twitclone.models import Bookmark, DirectMessage, Notification, Retweet, Tweet, User


def log_in(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_social_interactions_preserve_ownership_and_notification_lifecycle(client, app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        db.session.add_all([alice, bob])
        db.session.commit()
        tweet = Tweet(content="bob's tweet", user_id=bob.id)
        message = DirectMessage(
            content="hello alice", sender_id=bob.id, receiver_id=alice.id
        )
        db.session.add_all([tweet, message])
        db.session.commit()
        alice_id, bob_id, tweet_id, message_id = alice.id, bob.id, tweet.id, message.id

    log_in(client, alice_id)
    client.post("/follow/bob")
    client.post("/follow/bob")
    client.post(f"/bookmark/{tweet_id}")
    client.post(f"/bookmark/{tweet_id}")
    client.post(f"/retweet/{tweet_id}")
    client.post(f"/retweet/{tweet_id}")
    client.post(f"/reply/{message_id}", data={"content": "hello bob"})

    with app.app_context():
        alice = db.session.get(User, alice_id)
        assert alice.followed.filter_by(id=bob_id).count() == 1
        assert Bookmark.query.filter_by(user_id=alice_id, tweet_id=tweet_id).count() == 1
        assert Retweet.query.filter_by(user_id=alice_id, tweet_id=tweet_id).count() == 1
        assert DirectMessage.query.filter_by(
            content="hello bob", sender_id=alice_id, receiver_id=bob_id
        ).count() == 1
        notifications = Notification.query.filter_by(user_id=bob_id).all()
        assert {item.message for item in notifications} == {
            "alice followed you",
            "alice replied to your message",
        }
        assert all(item.read is False for item in notifications)

    log_in(client, bob_id)
    inbox_response = client.get("/messages")
    notification_response = client.get("/notifications")

    assert b"hello bob" in inbox_response.data
    assert b"alice followed you" in notification_response.data
    assert b"alice replied to your message" in notification_response.data
    with app.app_context():
        assert all(
            item.read for item in Notification.query.filter_by(user_id=bob_id).all()
        )
