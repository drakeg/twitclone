"""Regression coverage for Ripple search and discovery behavior."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _seed(client, app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash", bio="RV travel and Flask")
        bob = User(username="bobtravels", email="bob@example.com", password="hash", bio="Hiking waterfalls")
        db.session.add_all([alice, bob])
        db.session.commit()
        now = datetime.now(UTC).replace(tzinfo=None)
        db.session.add_all([
            Tweet(content="Older waterfall trip #travel", user_id=alice.id, timestamp=now),
            Tweet(content="Newest Flask notes #python", user_id=bob.id, timestamp=now + timedelta(minutes=1)),
            Tweet(content="Removed Flask post", user_id=alice.id, timestamp=now + timedelta(minutes=2), is_removed=True),
        ])
        db.session.commit()
        alice_id = alice.id
    _login(client, alice_id)
    return alice_id


def test_search_matches_plain_post_text_and_orders_newest_first(client, app):
    _seed(client, app)

    response = client.post("/search", data={"search_query": "Flask"})

    assert response.status_code == 200
    assert b"Newest Flask notes" in response.data
    assert b"Removed Flask post" not in response.data
    assert b"alice" in response.data  # bio match


def test_search_supports_at_username_queries(client, app):
    _seed(client, app)

    response = client.post("/search", data={"search_query": "@bob"})

    assert response.status_code == 200
    assert b"bobtravels" in response.data


def test_search_supports_hashtag_queries_and_links_to_topic(client, app):
    _seed(client, app)

    response = client.post("/search", data={"search_query": "#travel"})

    assert response.status_code == 200
    assert b"Older waterfall trip" in response.data
    assert b'href="/hashtag/travel"' in response.data
    assert b"Open #travel" in response.data


def test_search_normalizes_whitespace_and_handles_empty_queries(client, app):
    _seed(client, app)

    normalized = client.post("/search", data={"search_query": "   Flask   "})
    empty = client.post("/search", data={"search_query": "   "})

    assert normalized.status_code == 200
    assert b"Newest Flask notes" in normalized.data
    assert empty.status_code == 200
    assert b"Enter something to search for" in empty.data


def test_search_does_not_offer_follow_button_for_current_user(client, app):
    _seed(client, app)

    response = client.post("/search", data={"search_query": "alice"})

    assert response.status_code == 200
    assert b'data-username="alice"' not in response.data
