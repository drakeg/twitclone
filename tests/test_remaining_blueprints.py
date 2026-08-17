"""Focused tests for the final Sprint 2 Blueprint boundaries."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from flask import url_for

from twitclone.bookmarks.routes import bookmark, bookmarks
from twitclone.discovery.routes import hashtag, search
from twitclone.extensions import db
from twitclone.models import Bookmark, Notification, Tweet, User
from twitclone.profiles.routes import (
    edit_profile,
    follow,
    followers,
    following,
    profile,
    unfollow,
    unfollow_from_list,
)


def create_users(client, app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        db.session.add_all([alice, bob])
        db.session.commit()
        alice_id, bob_id = alice.id, bob.id
    with client.session_transaction() as session:
        session["_user_id"] = str(alice_id)
        session["_fresh"] = True
    return alice_id, bob_id


def test_final_blueprints_own_existing_routes(app):
    assert {"profiles", "discovery", "bookmarks"} <= set(app.blueprints)
    expected_views = {
        "follow": follow,
        "unfollow": unfollow,
        "profile": profile,
        "edit_profile": edit_profile,
        "followers": followers,
        "following": following,
        "unfollow_from_list": unfollow_from_list,
        "search": search,
        "hashtag": hashtag,
        "bookmark": bookmark,
        "bookmarks": bookmarks,
    }
    for endpoint, view in expected_views.items():
        assert app.view_functions[endpoint] is view

    with app.test_request_context():
        assert url_for("follow", username="bob") == "/follow/bob"
        assert url_for("unfollow", username="bob") == "/unfollow/bob"
        assert url_for("profile", username="bob") == "/profile/bob"
        assert url_for("edit_profile") == "/profile/edit"
        assert url_for("followers", username="bob") == "/followers/bob"
        assert url_for("following", username="bob") == "/following/bob"
        assert url_for("unfollow_from_list", user_id=2) == "/unfollow_from_list/2"
        assert url_for("search") == "/search"
        assert url_for("hashtag", hashtag="flask") == "/hashtag/flask"
        assert url_for("bookmark", tweet_id=1) == "/bookmark/1"
        assert url_for("bookmarks") == "/bookmarks"


def test_follow_and_unfollow_preserve_relationships_notifications_and_json(client, app):
    alice_id, bob_id = create_users(client, app)

    follow_response = client.post("/follow/bob")
    unfollow_response = client.post("/unfollow/bob")

    assert follow_response.get_json() == {
        "status": "success",
        "message": "You are now following bob.",
    }
    assert unfollow_response.get_json() == {
        "status": "success",
        "message": "You have unfollowed bob.",
    }
    with app.app_context():
        alice = db.session.get(User, alice_id)
        bob = db.session.get(User, bob_id)
        assert bob not in alice.followed
        assert [item.message for item in Notification.query.order_by(Notification.id)] == [
            "alice followed you",
            "alice unfollowed you",
        ]


def test_profile_edit_preserves_fields_and_redirect(client, app):
    alice_id, _ = create_users(client, app)

    response = client.post(
        "/profile/edit",
        data={
            "username": "alice-new",
            "email": "new@example.com",
            "bio": "updated bio",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile/alice-new"
    with app.app_context():
        alice = db.session.get(User, alice_id)
        assert (alice.username, alice.email, alice.bio) == (
            "alice-new",
            "new@example.com",
            "updated bio",
        )


def test_search_and_hashtag_preserve_results_and_order(client, app):
    alice_id, _ = create_users(client, app)
    now = datetime.now(UTC).replace(tzinfo=None)
    with app.app_context():
        db.session.add_all(
            [
                Tweet(content="older #flask", user_id=alice_id, timestamp=now),
                Tweet(
                    content="newer #flask",
                    user_id=alice_id,
                    timestamp=now + timedelta(minutes=1),
                ),
            ]
        )
        db.session.commit()

    search_response = client.post("/search", data={"search_query": "flask"})
    hashtag_response = client.get("/hashtag/flask")

    assert search_response.status_code == 200
    assert b"older " in search_response.data
    assert b"newer " in search_response.data
    assert b'href="/hashtag/flask"' in search_response.data
    assert hashtag_response.status_code == 200
    assert hashtag_response.data.index(b"newer ") < hashtag_response.data.index(b"older ")


def test_bookmarks_preserve_creation_filtering_order_and_redirect(client, app):
    alice_id, bob_id = create_users(client, app)
    with app.app_context():
        first = Tweet(content="first", user_id=alice_id)
        second = Tweet(content="second", user_id=alice_id)
        db.session.add_all([first, second])
        db.session.commit()
        first_id, second_id = first.id, second.id
        db.session.add(Bookmark(user_id=bob_id, tweet_id=first_id))
        db.session.commit()

    assert client.post(f"/bookmark/{first_id}").headers["Location"] == "/"
    assert client.post(f"/bookmark/{second_id}").headers["Location"] == "/"
    response = client.get("/bookmarks")

    assert response.status_code == 200
    assert response.data.index(b"second") < response.data.index(b"first")
    with app.app_context():
        assert Bookmark.query.filter_by(user_id=alice_id).count() == 2


def test_final_routes_still_require_login(client):
    for method, path in (
        (client.post, "/follow/bob"),
        (client.get, "/profile/bob"),
        (client.get, "/search"),
        (client.get, "/hashtag/flask"),
        (client.post, "/bookmark/1"),
        (client.get, "/bookmarks"),
    ):
        response = method(path)
        assert response.status_code == 302
        assert response.headers["Location"].startswith("/login?")


def test_legacy_module_no_longer_owns_routes_or_duplicate_utilities():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "@app.route" not in source
    assert "def gravatar(" not in source
    assert "def resize_image(" not in source
    assert "def get_trending_hashtags(" not in source
    assert "def make_clickable_links(" not in source
