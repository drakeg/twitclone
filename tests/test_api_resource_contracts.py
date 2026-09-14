"""Sprint 16 Story 16.4 bounded read/write post contract coverage."""

from twitclone.api.credentials import issue_api_credential
from twitclone.extensions import db
from twitclone.models import Tweet, User


def _user_and_token(app, scopes):
    with app.app_context():
        user = User(username="api_writer", email="api-writer@example.com", password="hash")
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
    assert response.headers["Location"] == f"/api/v1/posts/{payload['id']}"
    assert {topic["slug"] for topic in payload["topics"]} == {"aws", "automation"}

    follow_up = client.get(f"/api/v1/posts/{payload['id']}")
    assert follow_up.status_code == 200
    assert follow_up.get_json()["data"]["content"] == "API created post"


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
