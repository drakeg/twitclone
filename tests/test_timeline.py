"""Focused tests for the timeline Blueprint."""

from flask import url_for

from twitclone.extensions import bcrypt, db
from twitclone.models import Quote, Retweet, Tweet, User
from twitclone.timeline.routes import index, quote, retweet, tweet, uploaded_file


def create_logged_in_user(client, app):
    with app.app_context():
        user = User(
            username="alice",
            email="alice@example.com",
            password=bcrypt.generate_password_hash("secret").decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
    return user_id


def test_timeline_blueprint_owns_existing_routes(app):
    assert "timeline" in app.blueprints
    assert app.view_functions["index"] is index
    assert app.view_functions["tweet"] is tweet
    assert app.view_functions["uploaded_file"] is uploaded_file
    assert app.view_functions["retweet"] is retweet
    assert app.view_functions["quote"] is quote

    with app.test_request_context():
        assert url_for("index") == "/"
        assert url_for("tweet") == "/tweet"
        assert url_for("uploaded_file", filename="photo.jpg") == "/uploads/photo.jpg"
        assert url_for("retweet", tweet_id=1) == "/retweet/1"
        assert url_for("quote", tweet_id=1) == "/quote/1"


def test_tweet_creation_preserves_behavior_and_redirect(client, app):
    user_id = create_logged_in_user(client, app)

    response = client.post("/tweet", data={"content": "hello timeline"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    with app.app_context():
        created = Tweet.query.one()
        assert created.content == "hello timeline"
        assert created.user_id == user_id


def test_retweet_and_quote_preserve_behavior(client, app):
    user_id = create_logged_in_user(client, app)
    with app.app_context():
        original = Tweet(content="original", user_id=user_id)
        db.session.add(original)
        db.session.commit()
        tweet_id = original.id

    retweet_response = client.post(f"/retweet/{tweet_id}")
    quote_response = client.post(f"/quote/{tweet_id}", data={"content": "my take"})

    assert retweet_response.status_code == 302
    assert retweet_response.headers["Location"] == "/"
    assert quote_response.status_code == 302
    assert quote_response.headers["Location"] == "/"
    with app.app_context():
        assert Retweet.query.filter_by(user_id=user_id, tweet_id=tweet_id).one()
        assert Quote.query.filter_by(user_id=user_id, tweet_id=tweet_id).one().content == "my take"


def test_timeline_writes_still_require_login(client):
    response = client.post("/tweet", data={"content": "not allowed"})

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?")
