"""Authorization and ownership boundaries for post writes."""

import pytest

from twitclone.extensions import bcrypt, db
from twitclone.models import Bookmark, Quote, Retweet, Tweet, User


def create_users(app):
    with app.app_context():
        users = [
            User(
                username=username,
                email=f"{username}@example.com",
                password=bcrypt.generate_password_hash("secret").decode("utf-8"),
            )
            for username in ("alice", "bob")
        ]
        db.session.add_all(users)
        db.session.commit()
        return users[0].id, users[1].id


def log_in(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


@pytest.mark.parametrize(
    ("path", "data"),
    [
        ("/tweet", {"content": "anonymous tweet"}),
        ("/retweet/1", None),
        ("/quote/1", {"content": "anonymous quote"}),
        ("/bookmark/1", None),
    ],
)
def test_anonymous_users_cannot_create_post_interactions(client, app, path, data):
    response = client.post(path, data=data)

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?")
    with app.app_context():
        assert Tweet.query.count() == 0
        assert Retweet.query.count() == 0
        assert Quote.query.count() == 0
        assert Bookmark.query.count() == 0


def test_tweet_owner_always_comes_from_authenticated_user(client, app):
    alice_id, bob_id = create_users(app)
    log_in(client, alice_id)

    response = client.post(
        "/tweet",
        data={"content": "owned by alice", "user_id": bob_id},
    )

    assert response.status_code == 302
    with app.app_context():
        created = Tweet.query.one()
        assert created.user_id == alice_id
        assert created.user_id != bob_id


@pytest.mark.parametrize(
    ("path_template", "data", "model"),
    [
        ("/retweet/{tweet_id}", None, Retweet),
        ("/quote/{tweet_id}", {"content": "alice's take"}, Quote),
        ("/bookmark/{tweet_id}", None, Bookmark),
    ],
)
def test_interaction_owner_always_comes_from_authenticated_user(
    client, app, path_template, data, model
):
    alice_id, bob_id = create_users(app)
    with app.app_context():
        original = Tweet(content="bob's tweet", user_id=bob_id)
        db.session.add(original)
        db.session.commit()
        tweet_id = original.id
    log_in(client, alice_id)

    submitted_data = dict(data or {})
    submitted_data["user_id"] = bob_id
    response = client.post(
        path_template.format(tweet_id=tweet_id),
        data=submitted_data,
    )

    assert response.status_code == 302
    with app.app_context():
        created = model.query.one()
        assert created.user_id == alice_id
        assert created.user_id != bob_id
        assert created.tweet_id == tweet_id
