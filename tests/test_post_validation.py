"""Post-content validation regression tests."""

from io import BytesIO
from pathlib import Path

import pytest

from twitclone.extensions import db
from twitclone.models import Quote, Tweet, User
from twitclone.timeline.validation import POST_CONTENT_LIMIT, validate_post_content


def create_logged_in_user(client, app):
    with app.app_context():
        user = User(username="alice", email="alice@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
    return user_id


def latest_flash(client):
    with client.session_transaction() as session:
        return session["_flashes"][-1]


@pytest.mark.parametrize("content", [None, "", "   \t\n"])
def test_validator_rejects_missing_empty_and_whitespace_content(content):
    assert validate_post_content(content, post_type="Tweet") == (
        "Tweet content is required."
    )


def test_validator_accepts_boundary_and_preserves_valid_content():
    content = " " + ("x" * (POST_CONTENT_LIMIT - 2)) + " "

    assert len(content) == POST_CONTENT_LIMIT
    assert validate_post_content(content, post_type="Tweet") is None


def test_validator_rejects_content_above_boundary():
    assert validate_post_content("x" * 145, post_type="Quote") == (
        "Quote content exceeds 144 characters."
    )


@pytest.mark.parametrize("data", [{}, {"content": ""}, {"content": "   "}])
def test_tweet_rejects_required_content_without_database_or_file_writes(
    client, app, data
):
    create_logged_in_user(client, app)
    filename = "invalid-content-upload.png"
    submitted = {
        **data,
        "image": (BytesIO(b"not an image"), filename),
    }

    response = client.post("/tweet", data=submitted)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert latest_flash(client) == ("danger", "Tweet content is required.")
    with app.app_context():
        assert Tweet.query.count() == 0
        upload_path = app.config["UPLOAD_FOLDER"]
    assert not Path(upload_path, filename).exists()


def test_tweet_accepts_exactly_144_characters_and_rejects_145(client, app):
    user_id = create_logged_in_user(client, app)
    accepted = "x" * 144

    accepted_response = client.post("/tweet", data={"content": accepted})
    rejected_response = client.post("/tweet", data={"content": "x" * 145})

    assert accepted_response.headers["Location"] == "/"
    assert rejected_response.headers["Location"] == "/"
    assert latest_flash(client) == (
        "danger",
        "Tweet content exceeds 144 characters.",
    )
    with app.app_context():
        tweets = Tweet.query.all()
        assert [(tweet.content, tweet.user_id) for tweet in tweets] == [
            (accepted, user_id)
        ]


@pytest.mark.parametrize(
    ("content", "expected_message"),
    [
        (None, "Quote content is required."),
        ("", "Quote content is required."),
        ("   ", "Quote content is required."),
        ("x" * 145, "Quote content exceeds 144 characters."),
    ],
)
def test_quote_rejects_invalid_content_without_writes(
    client, app, content, expected_message
):
    user_id = create_logged_in_user(client, app)
    with app.app_context():
        original = Tweet(content="original", user_id=user_id)
        db.session.add(original)
        db.session.commit()
        tweet_id = original.id
    data = {} if content is None else {"content": content}

    response = client.post(f"/quote/{tweet_id}", data=data)

    assert response.status_code == 400
    assert expected_message.encode() in response.data
    with app.app_context():
        assert Quote.query.count() == 0


def test_quote_accepts_exactly_144_characters(client, app):
    user_id = create_logged_in_user(client, app)
    with app.app_context():
        original = Tweet(content="original", user_id=user_id)
        db.session.add(original)
        db.session.commit()
        tweet_id = original.id
    content = "q" * 144

    response = client.post(f"/quote/{tweet_id}", data={"content": content})

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    with app.app_context():
        assert Quote.query.one().content == content


def test_templates_expose_matching_browser_constraints(client):
    index_response = client.get("/")

    assert b'name="content"' in index_response.data
    assert b'maxlength="144"' in index_response.data
    assert b"required" in index_response.data
