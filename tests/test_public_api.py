"""Sprint 16 Story 16.1 public API contract coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.spaces.models import Space, SpacePost
from twitclone.topic_models import associate_topics


def _user(app, suffix="author"):
    with app.app_context():
        user = User(username=f"api_{suffix}", email=f"api-{suffix}@example.com", password="hash")
        db.session.add(user); db.session.commit(); return user.id


def test_api_index_declares_versioned_read_only_preview(client):
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert response.get_json() == {"name": "Ripple Public API", "version": "v1", "status": "read-only-preview", "documentation": "/api/v1/"}


def test_public_post_contract_exposes_bounded_fields(client, app):
    user_id = _user(app)
    with app.app_context():
        published_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5)
        tweet = Tweet(content="API-visible post", user_id=user_id, timestamp=published_at)
        db.session.add(tweet); db.session.flush(); associate_topics(tweet, explicit_raw="AWS", content=tweet.content); db.session.commit(); tweet_id = tweet.id
    response = client.get(f"/api/v1/posts/{tweet_id}")
    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["id"] == tweet_id
    assert payload["type"] == "post"
    assert payload["content"] == "API-visible post"
    assert payload["author"]["username"] == "api_author"
    assert payload["url"] == f"/post/{tweet_id}"
    assert payload["published_at"].endswith("Z")
    assert payload["topics"] == [{"name": "AWS", "slug": "aws", "source": "explicit"}]
    assert set(payload) == {"id", "type", "content", "author", "published_at", "topics", "url"}


def test_removed_and_future_posts_fail_closed(client, app):
    user_id = _user(app, "visibility")
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        removed = Tweet(content="removed", user_id=user_id, is_removed=True)
        future = Tweet(content="future", user_id=user_id, scheduled_at=now + timedelta(days=1))
        db.session.add_all([removed, future]); db.session.commit(); ids = (removed.id, future.id)
    for tweet_id in ids:
        response = client.get(f"/api/v1/posts/{tweet_id}")
        assert response.status_code == 404
        assert response.get_json() == {"error": {"code": "post_not_found", "message": "The requested public post was not found."}}


def test_space_scoped_post_is_not_exposed_by_global_public_api(client, app):
    user_id = _user(app, "space")
    with app.app_context():
        space = Space(slug="api-space", name="API Space", description="Space-scoped content", owner_id=user_id)
        tweet = Tweet(content="space-only post", user_id=user_id)
        db.session.add_all([space, tweet]); db.session.flush(); db.session.add(SpacePost(space_id=space.id, tweet_id=tweet.id)); db.session.commit(); tweet_id = tweet.id
    response = client.get(f"/api/v1/posts/{tweet_id}")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "post_not_found"


def test_public_post_endpoint_is_read_only(client, app):
    user_id = _user(app, "readonly")
    with app.app_context():
        tweet = Tweet(content="read only", user_id=user_id); db.session.add(tweet); db.session.commit(); tweet_id = tweet.id
    response = client.post(f"/api/v1/posts/{tweet_id}", json={"content": "changed"})
    assert response.status_code == 405
