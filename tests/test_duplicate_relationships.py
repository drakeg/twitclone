"""Duplicate social relationship prevention tests."""

from sqlalchemy.exc import IntegrityError

from twitclone.extensions import db
from twitclone.models import Bookmark, Notification, Retweet, Tweet, User


def create_users_and_tweet(client, app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        db.session.add_all([alice, bob])
        db.session.commit()
        tweet = Tweet(content="bob's tweet", user_id=bob.id)
        db.session.add(tweet)
        db.session.commit()
        alice_id, bob_id, tweet_id = alice.id, bob.id, tweet.id
    with client.session_transaction() as session:
        session["_user_id"] = str(alice_id)
        session["_fresh"] = True
    return alice_id, bob_id, tweet_id


def test_repeated_follow_is_idempotent_and_notifies_once(client, app):
    alice_id, bob_id, _ = create_users_and_tweet(client, app)

    first = client.post("/follow/bob")
    second = client.post("/follow/bob")

    assert first.get_json()["status"] == "success"
    assert second.get_json()["status"] == "success"
    with app.app_context():
        alice = db.session.get(User, alice_id)
        assert alice.followed.filter_by(id=bob_id).count() == 1
        assert Notification.query.filter_by(user_id=bob_id).count() == 1


def test_repeated_unfollow_is_idempotent_and_notifies_once(client, app):
    _, bob_id, _ = create_users_and_tweet(client, app)
    client.post("/follow/bob")

    first = client.post("/unfollow/bob")
    second = client.post("/unfollow/bob")

    assert first.get_json()["status"] == "success"
    assert second.get_json()["status"] == "success"
    with app.app_context():
        messages = [
            item.message
            for item in Notification.query.filter_by(user_id=bob_id).order_by(
                Notification.id
            )
        ]
        assert messages == ["alice followed you", "alice unfollowed you"]


def test_repeated_bookmark_creates_one_relationship(client, app):
    alice_id, _, tweet_id = create_users_and_tweet(client, app)

    first = client.post(f"/bookmark/{tweet_id}")
    second = client.post(f"/bookmark/{tweet_id}")

    assert first.headers["Location"] == "/"
    assert second.headers["Location"] == "/"
    with app.app_context():
        assert Bookmark.query.filter_by(user_id=alice_id, tweet_id=tweet_id).count() == 1


def test_repeated_retweet_creates_one_relationship(client, app):
    alice_id, _, tweet_id = create_users_and_tweet(client, app)

    first = client.post(f"/retweet/{tweet_id}")
    second = client.post(f"/retweet/{tweet_id}")

    assert first.headers["Location"] == "/"
    assert second.headers["Location"] == "/"
    with app.app_context():
        assert Retweet.query.filter_by(user_id=alice_id, tweet_id=tweet_id).count() == 1


def test_database_rejects_duplicate_bookmarks_and_retweets(client, app):
    alice_id, _, tweet_id = create_users_and_tweet(client, app)

    for model in (Bookmark, Retweet):
        with app.app_context():
            db.session.add_all(
                [
                    model(user_id=alice_id, tweet_id=tweet_id),
                    model(user_id=alice_id, tweet_id=tweet_id),
                ]
            )
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            else:
                raise AssertionError(f"{model.__name__} accepted a duplicate relationship")
