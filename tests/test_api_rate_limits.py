"""Sprint 16 Story 16.3 API rate-limit and abuse-boundary coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.api.credentials import issue_api_credential
from twitclone.api.rate_limits import ApiRateLimitBucket, consume_rate_limit
from twitclone.extensions import db
from twitclone.models import User


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _credential(app, username="rate_user"):
    with app.app_context():
        user = User(
            username=username,
            email=f"{username}@example.com",
            password="hash",
        )
        db.session.add(user)
        db.session.flush()
        credential, raw_token = issue_api_credential(
            user_id=user.id,
            label="rate test",
            scopes={"posts:read"},
        )
        db.session.commit()
        return credential.id, raw_token


def test_public_read_limit_returns_bounded_429_and_headers(client, app):
    app.config["API_PUBLIC_READ_LIMIT"] = 2
    app.config["API_RATE_LIMIT_WINDOW_SECONDS"] = 60

    first = client.get("/api/v1/")
    second = client.get("/api/v1/")
    blocked = client.get("/api/v1/")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "2"
    assert first.headers["X-RateLimit-Remaining"] == "1"
    assert second.status_code == 200
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert blocked.status_code == 429
    assert blocked.get_json()["error"]["code"] == "rate_limited"
    assert int(blocked.headers["Retry-After"]) >= 1
    assert blocked.headers["X-RateLimit-Remaining"] == "0"


def test_rate_limit_bucket_does_not_store_raw_client_identifier(client, app):
    client.get("/api/v1/")

    with app.app_context():
        bucket = ApiRateLimitBucket.query.filter_by(bucket_type="public_read").one()
        assert bucket.subject_hash != "127.0.0.1"
        assert len(bucket.subject_hash) == 64


def test_invalid_bearer_attempts_have_tighter_client_budget(client, app):
    app.config["API_INVALID_TOKEN_LIMIT"] = 2

    first = client.get("/api/v1/account")
    second = client.get("/api/v1/account", headers={"Authorization": "Bearer nope"})
    blocked = client.get("/api/v1/account", headers={"Authorization": "Basic nope"})

    assert first.status_code == 401
    assert first.get_json()["error"]["code"] == "invalid_token"
    assert second.status_code == 401
    assert blocked.status_code == 429
    assert blocked.get_json()["error"]["code"] == "rate_limited"


def test_valid_credential_has_independent_rate_budget(client, app):
    _, raw_token = _credential(app)
    app.config["API_CREDENTIAL_LIMIT"] = 2
    headers = {"Authorization": f"Bearer {raw_token}"}

    first = client.get("/api/v1/account", headers=headers)
    second = client.get("/api/v1/account", headers=headers)
    blocked = client.get("/api/v1/account", headers=headers)

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "2"
    assert second.status_code == 200
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert blocked.status_code == 429
    assert blocked.get_json()["error"]["code"] == "rate_limited"


def test_different_credentials_do_not_share_credential_budget(client, app):
    _, first_token = _credential(app, "rate_first")
    _, second_token = _credential(app, "rate_second")
    app.config["API_CREDENTIAL_LIMIT"] = 1

    first = client.get(
        "/api/v1/account",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    second = client.get(
        "/api/v1/account",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200


def test_fixed_window_resets_after_expiration(app):
    now = _utcnow().replace(second=0, microsecond=0)
    with app.app_context():
        first = consume_rate_limit(
            bucket_type="test",
            subject="client-a",
            secret_key="test-secret",
            limit=1,
            window_seconds=60,
            now=now,
        )
        blocked = consume_rate_limit(
            bucket_type="test",
            subject="client-a",
            secret_key="test-secret",
            limit=1,
            window_seconds=60,
            now=now + timedelta(seconds=30),
        )
        reset = consume_rate_limit(
            bucket_type="test",
            subject="client-a",
            secret_key="test-secret",
            limit=1,
            window_seconds=60,
            now=now + timedelta(seconds=61),
        )

    assert first.allowed is True
    assert blocked.allowed is False
    assert reset.allowed is True
