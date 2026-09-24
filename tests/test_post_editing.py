"""Sprint 21 owner-only original post editing coverage."""

from datetime import UTC, datetime

from twitclone.extensions import db
from twitclone.models import Notification, Tweet, User
from twitclone.topic_models import Topic, TweetTopic


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _users_and_post(app, content="original @bob"):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        carol = User(username="carol", email="carol@example.com", password="hash")
        db.session.add_all([alice, bob, carol])
        db.session.flush()
        created_at = datetime(2026, 9, 23, 20, 0, tzinfo=UTC).replace(tzinfo=None)
        tweet = Tweet(
            content=content,
            user_id=alice.id,
            timestamp=created_at,
            image="thumb_example.png",
            original_image="example.png",
        )
        db.session.add(tweet)
        db.session.commit()
        return alice.id, bob.id, carol.id, tweet.id, created_at


def test_anonymous_user_cannot_open_edit_form(client, app):
    _, _, _, tweet_id, _ = _users_and_post(app)

    response = client.get(f"/post/{tweet_id}/edit")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?")


def test_non_owner_cannot_view_or_submit_edit(client, app):
    _, bob_id, _, tweet_id, _ = _users_and_post(app)
    _login(client, bob_id)

    get_response = client.get(f"/post/{tweet_id}/edit")
    post_response = client.post(
        f"/post/{tweet_id}/edit",
        data={"content": "attempted takeover"},
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).content == "original @bob"


def test_owner_can_edit_text_without_changing_publish_identity_or_media(client, app):
    alice_id, _, _, tweet_id, created_at = _users_and_post(app)
    _login(client, alice_id)

    response = client.post(
        f"/post/{tweet_id}/edit",
        data={"content": "updated post text"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/post/{tweet_id}")
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.content == "updated post text"
        assert tweet.user_id == alice_id
        assert tweet.timestamp == created_at
        assert tweet.image == "thumb_example.png"
        assert tweet.original_image == "example.png"
        assert tweet.edited_at is not None


def test_invalid_edit_is_rejected_without_mutating_post(client, app):
    alice_id, _, _, tweet_id, _ = _users_and_post(app)
    _login(client, alice_id)

    response = client.post(
        f"/post/{tweet_id}/edit",
        data={"content": "x" * 145},
    )

    assert response.status_code == 400
    assert b"Tweet content exceeds 144 characters." in response.data
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.content == "original @bob"
        assert tweet.edited_at is None


def test_noop_edit_does_not_mark_post_edited(client, app):
    alice_id, _, _, tweet_id, _ = _users_and_post(app, content="same text")
    _login(client, alice_id)

    response = client.post(
        f"/post/{tweet_id}/edit",
        data={"content": "same text"},
    )

    assert response.status_code == 302
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.content == "same text"
        assert tweet.edited_at is None


def test_edit_notifies_only_newly_added_mentions(client, app):
    alice_id, bob_id, carol_id, tweet_id, _ = _users_and_post(app)
    _login(client, alice_id)

    response = client.post(
        f"/post/{tweet_id}/edit",
        data={"content": "still @bob and now @carol"},
    )

    assert response.status_code == 302
    with app.app_context():
        assert Notification.query.filter_by(user_id=bob_id).count() == 0
        carol_notices = Notification.query.filter_by(user_id=carol_id).all()
        assert [item.message for item in carol_notices] == [
            "alice mentioned you in a post"
        ]
        assert carol_notices[0].tweet_id == tweet_id


def test_owner_detail_exposes_edit_control_and_edited_marker(client, app):
    alice_id, _, _, tweet_id, _ = _users_and_post(app, content="before")
    _login(client, alice_id)
    client.post(f"/post/{tweet_id}/edit", data={"content": "after"})

    response = client.get(f"/post/{tweet_id}")

    assert response.status_code == 200
    assert b"Edit post" in response.data
    assert b"Edited" in response.data
    assert b"after" in response.data


def test_non_owner_detail_does_not_expose_edit_control(client, app):
    _, bob_id, _, tweet_id, _ = _users_and_post(app)
    _login(client, bob_id)

    response = client.get(f"/post/{tweet_id}")

    assert response.status_code == 200
    assert b">Edit post<" not in response.data



def test_edit_refreshes_hashtag_topics_but_preserves_explicit_topics(client, app):
    alice_id, _, _, tweet_id, _ = _users_and_post(app, content="before #old")
    with app.app_context():
        explicit = Topic(name="AWS", slug="aws")
        old_hashtag = Topic(name="old", slug="old")
        db.session.add_all([explicit, old_hashtag])
        db.session.flush()
        db.session.add_all(
            [
                TweetTopic(tweet_id=tweet_id, topic_id=explicit.id, source="explicit"),
                TweetTopic(tweet_id=tweet_id, topic_id=old_hashtag.id, source="hashtag"),
            ]
        )
        db.session.commit()
    _login(client, alice_id)

    response = client.post(
        f"/post/{tweet_id}/edit",
        data={"content": "after #new"},
    )

    assert response.status_code == 302
    with app.app_context():
        rows = TweetTopic.query.filter_by(tweet_id=tweet_id).all()
        associations = {(row.topic.slug, row.source) for row in rows}
        assert ("aws", "explicit") in associations
        assert ("new", "hashtag") in associations
        assert ("old", "hashtag") not in associations



def test_future_scheduled_post_is_not_editable_through_published_post_flow(client, app):
    alice_id, _, _, tweet_id, _ = _users_and_post(app, content="scheduled")
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        tweet.scheduled_at = datetime(2099, 1, 1, 12, 0)
        db.session.commit()
    _login(client, alice_id)

    get_response = client.get(f"/post/{tweet_id}/edit")
    post_response = client.post(
        f"/post/{tweet_id}/edit",
        data={"content": "changed"},
    )

    assert get_response.status_code == 404
    assert post_response.status_code == 404
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).content == "scheduled"
