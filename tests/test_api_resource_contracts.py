"""Sprint 16 Story 16.4 bounded read/write post contract coverage."""

from twitclone.api.credentials import issue_api_credential
from twitclone.extensions import db
from twitclone.models import Notification, Tweet, User
from twitclone.topic_models import Topic, TweetTopic


def _etag(client, tweet_id):
    response = client.get(f"/api/v1/posts/{tweet_id}")
    assert response.status_code == 200
    assert response.headers["ETag"].startswith('"')
    return response.headers["ETag"]


def _user_and_token(app, scopes, username="api_writer"):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user); db.session.flush()
        credential, raw_token = issue_api_credential(
            user_id=user.id,
            label="resource-contract-test",
            scopes=scopes,
        )
        user_id = user.id
        credential_id = credential.id
        db.session.commit()
        return user_id, credential_id, raw_token


def test_posts_write_scope_can_create_public_post(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:read", "posts:write"})
    response = client.post(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={
            "content": "API created post",
            "conversation_intent": "question",
            "topics": ["AWS", "Automation"],
        },
    )
    assert response.status_code == 201
    payload = response.get_json()["data"]
    assert payload["content"] == "API created post"
    assert payload["author"]["id"] == user_id
    assert payload["edited_at"] is None
    assert response.headers["Location"] == f"/api/v1/posts/{payload['id']}"
    assert response.headers["ETag"]
    assert {topic["slug"] for topic in payload["topics"]} == {"aws", "automation"}

    follow_up = client.get(f"/api/v1/posts/{payload['id']}")
    assert follow_up.status_code == 200
    assert follow_up.get_json()["data"]["content"] == "API created post"
    assert follow_up.headers["ETag"] == response.headers["ETag"]


def test_posts_read_scope_cannot_create_post(client, app):
    _, _, raw_token = _user_and_token(app, {"posts:read"})
    response = client.post(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={"content": "should not exist"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "insufficient_scope"
    with app.app_context():
        assert Tweet.query.filter_by(content="should not exist").first() is None


def test_post_write_validation_fails_closed(client, app):
    _, _, raw_token = _user_and_token(app, {"posts:write"})
    response = client.post(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={"content": "", "topics": ["one", "two", "three", "four", "five", "six"]},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_post"


def test_post_write_rejects_non_json_body(client, app):
    _, _, raw_token = _user_and_token(app, {"posts:write"})
    response = client.post(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {raw_token}", "Content-Type": "text/plain"},
        data="not-json",
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_post"


def test_api_index_advertises_bounded_write_scope(client):
    response = client.get("/api/v1/")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "limited-write-preview"
    assert payload["authentication"]["supported_scopes"] == ["posts:read", "posts:write"]



def test_public_post_contract_exposes_edit_timestamp(client, app):
    user_id, _, _ = _user_and_token(app, {"posts:read"})
    with app.app_context():
        tweet = Tweet(content="edited API post", user_id=user_id)
        db.session.add(tweet)
        db.session.flush()
        tweet.edited_at = tweet.timestamp
        db.session.commit()
        tweet_id = tweet.id

    response = client.get(f"/api/v1/posts/{tweet_id}")

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["content"] == "edited API post"
    assert payload["edited_at"] is not None



def test_posts_write_scope_can_edit_owned_public_post(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:write"}, username="api_editor")
    with app.app_context():
        bob = User(username="api_bob", email="api_bob@example.com", password="hash")
        carol = User(username="api_carol", email="api_carol@example.com", password="hash")
        db.session.add_all([bob, carol])
        db.session.flush()
        tweet = Tweet(content="before @api_bob #old", user_id=user_id)
        db.session.add(tweet)
        db.session.flush()
        explicit = Topic(name="AWS", slug="aws")
        old_hashtag = Topic(name="old", slug="old")
        db.session.add_all([explicit, old_hashtag])
        db.session.flush()
        db.session.add_all([
            TweetTopic(tweet_id=tweet.id, topic_id=explicit.id, source="explicit"),
            TweetTopic(tweet_id=tweet.id, topic_id=old_hashtag.id, source="hashtag"),
        ])
        db.session.commit()
        tweet_id = tweet.id
        bob_id = bob.id
        carol_id = carol.id

    etag = _etag(client, tweet_id)
    response = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": etag},
        json={"content": "after @api_bob @api_carol #new"},
    )

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["content"] == "after @api_bob @api_carol #new"
    assert payload["edited_at"] is not None
    assert {item["slug"] for item in payload["topics"]} == {"aws", "new"}
    with app.app_context():
        assert Notification.query.filter_by(user_id=bob_id).count() == 0
        notices = Notification.query.filter_by(user_id=carol_id).all()
        assert [item.message for item in notices] == ["api_editor mentioned you in a post"]


def test_api_edit_rejects_non_owner_and_read_only_credential(client, app):
    owner_id, _, owner_token = _user_and_token(app, {"posts:write"}, username="api_owner")
    _, _, other_token = _user_and_token(app, {"posts:write"}, username="api_other")
    _, _, read_token = _user_and_token(app, {"posts:read"}, username="api_reader")
    with app.app_context():
        tweet = Tweet(content="owner content", user_id=owner_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    forbidden = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"content": "takeover"},
    )
    read_only = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {read_token}"},
        json={"content": "read scope write"},
    )

    assert forbidden.status_code == 403
    assert forbidden.get_json()["error"]["code"] == "post_not_owned"
    assert read_only.status_code == 403
    assert read_only.get_json()["error"]["code"] == "insufficient_scope"
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).content == "owner content"


def test_api_edit_accepts_only_content_and_noop_preserves_unedited_state(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:write"}, username="api_noop")
    with app.app_context():
        tweet = Tweet(content="same text", user_id=user_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    etag = _etag(client, tweet_id)
    invalid = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": etag},
        json={"content": "changed", "topics": ["unexpected"]},
    )
    noop = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": etag},
        json={"content": "same text"},
    )

    assert invalid.status_code == 400
    assert invalid.get_json()["error"]["code"] == "invalid_post"
    assert noop.status_code == 200
    assert noop.get_json()["data"]["edited_at"] is None
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.content == "same text"
        assert tweet.edited_at is None


def test_posts_write_scope_can_soft_remove_owned_public_post(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:write"}, username="api_remover")
    with app.app_context():
        tweet = Tweet(content="remove through API", user_id=user_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    etag = _etag(client, tweet_id)
    response = client.delete(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": etag},
    )

    assert response.status_code == 204
    assert response.data == b""
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.is_removed is True
        assert tweet.removed_at is not None
        assert tweet.removed_by_id == user_id
        assert tweet.removal_reason == "Removed by author."

    follow_up = client.get(f"/api/v1/posts/{tweet_id}")
    assert follow_up.status_code == 404


def test_api_remove_rejects_non_owner_and_read_only_credential(client, app):
    owner_id, _, _ = _user_and_token(app, {"posts:write"}, username="remove_owner")
    _, _, other_token = _user_and_token(app, {"posts:write"}, username="remove_other")
    _, _, read_token = _user_and_token(app, {"posts:read"}, username="remove_reader")
    with app.app_context():
        tweet = Tweet(content="protected lifecycle", user_id=owner_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    forbidden = client.delete(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    read_only = client.delete(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {read_token}"},
    )

    assert forbidden.status_code == 403
    assert forbidden.get_json()["error"]["code"] == "post_not_owned"
    assert read_only.status_code == 403
    assert read_only.get_json()["error"]["code"] == "insufficient_scope"
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).is_removed is False



def test_api_mutations_hide_future_scheduled_post_existence(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:write"}, username="api_scheduled")
    with app.app_context():
        from datetime import datetime

        tweet = Tweet(
            content="future hidden",
            user_id=user_id,
            scheduled_at=datetime(2099, 1, 1, 12, 0),
        )
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    edit = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={"content": "should stay hidden"},
    )
    remove = client.delete(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}"},
    )

    assert edit.status_code == 404
    assert edit.get_json()["error"]["code"] == "post_not_found"
    assert remove.status_code == 404
    assert remove.get_json()["error"]["code"] == "post_not_found"
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.content == "future hidden"
        assert tweet.is_removed is False



def test_api_lifecycle_mutations_require_if_match(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:write"}, username="api_precondition")
    with app.app_context():
        tweet = Tweet(content="conditional", user_id=user_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    edit = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={"content": "changed"},
    )
    remove = client.delete(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}"},
    )

    assert edit.status_code == 428
    assert edit.get_json()["error"]["code"] == "precondition_required"
    assert edit.headers["ETag"]
    assert remove.status_code == 428
    assert remove.get_json()["error"]["code"] == "precondition_required"
    assert remove.headers["ETag"]

    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.content == "conditional"
        assert tweet.is_removed is False


def test_api_edit_rejects_stale_etag_without_lost_update(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:write"}, username="api_stale")
    with app.app_context():
        tweet = Tweet(content="version one", user_id=user_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    first_etag = _etag(client, tweet_id)
    first = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": first_etag},
        json={"content": "version two"},
    )
    assert first.status_code == 200
    assert first.headers["ETag"] != first_etag

    stale = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": first_etag},
        json={"content": "version three"},
    )

    assert stale.status_code == 412
    assert stale.get_json()["error"]["code"] == "precondition_failed"
    assert stale.headers["ETag"] == first.headers["ETag"]
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).content == "version two"


def test_api_remove_rejects_stale_etag(client, app):
    user_id, _, raw_token = _user_and_token(app, {"posts:write"}, username="api_remove_stale")
    with app.app_context():
        tweet = Tweet(content="remove race", user_id=user_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    stale_etag = _etag(client, tweet_id)
    edit = client.patch(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": stale_etag},
        json={"content": "changed before remove"},
    )
    assert edit.status_code == 200

    remove = client.delete(
        f"/api/v1/posts/{tweet_id}",
        headers={"Authorization": f"Bearer {raw_token}", "If-Match": stale_etag},
    )

    assert remove.status_code == 412
    assert remove.get_json()["error"]["code"] == "precondition_failed"
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).is_removed is False
