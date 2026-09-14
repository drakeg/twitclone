"""Sprint 16 Story 16.2 scoped API credential coverage."""

from datetime import UTC, datetime, timedelta

import pytest

from twitclone.api.credentials import (
    ApiCredential,
    DEFAULT_CREDENTIAL_LIFETIME_DAYS,
    issue_api_credential,
    revoke_api_credential,
)
from twitclone.extensions import db
from twitclone.models import User


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _user(app):
    with app.app_context():
        user = User(username="api_user", email="api-user@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _issue(app, user_id, **kwargs):
    with app.app_context():
        credential, raw_token = issue_api_credential(
            user_id=user_id,
            label=kwargs.pop("label", "local integration"),
            scopes=kwargs.pop("scopes", {"posts:read"}),
            **kwargs,
        )
        credential_id = credential.id
        db.session.commit()
        return credential_id, raw_token


def test_issued_token_is_hashed_and_defaults_to_ninety_day_expiry(app):
    user_id = _user(app)
    before = _utcnow()
    credential_id, raw_token = _issue(app, user_id)

    with app.app_context():
        credential = db.session.get(ApiCredential, credential_id)
        assert credential.token_digest != raw_token
        assert raw_token not in credential.token_digest
        assert credential.token_prefix == raw_token[:12]
        assert credential.scope_set == {"posts:read"}
        assert before + timedelta(days=DEFAULT_CREDENTIAL_LIFETIME_DAYS - 1) < credential.expires_at
        assert credential.expires_at <= _utcnow() + timedelta(days=DEFAULT_CREDENTIAL_LIFETIME_DAYS, seconds=5)


def test_credential_lifetime_cannot_exceed_one_year(app):
    user_id = _user(app)
    with app.app_context(), pytest.raises(ValueError, match="cannot exceed 365 days"):
        issue_api_credential(
            user_id=user_id,
            label="too long",
            scopes={"posts:read"},
            expires_at=_utcnow() + timedelta(days=366),
        )


def test_unsupported_scope_is_rejected(app):
    user_id = _user(app)
    with app.app_context(), pytest.raises(ValueError, match="supported scope"):
        issue_api_credential(user_id=user_id, label="writer", scopes={"posts:write"})


def test_api_account_requires_bearer_token_even_with_browser_session(client, app):
    user_id = _user(app)
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

    response = client.get("/api/v1/account")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_token"


def test_valid_bearer_token_authenticates_and_records_last_use(client, app):
    user_id = _user(app)
    credential_id, raw_token = _issue(app, user_id)

    response = client.get("/api/v1/account", headers={"Authorization": f"Bearer {raw_token}"})
    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["user"]["username"] == "api_user"
    assert payload["credential"]["id"] == credential_id
    assert payload["credential"]["scopes"] == ["posts:read"]

    with app.app_context():
        assert db.session.get(ApiCredential, credential_id).last_used_at is not None


def test_revoked_token_fails_closed(client, app):
    user_id = _user(app)
    credential_id, raw_token = _issue(app, user_id)
    with app.app_context():
        revoke_api_credential(db.session.get(ApiCredential, credential_id))

    response = client.get("/api/v1/account", headers={"Authorization": f"Bearer {raw_token}"})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_token"


def test_expired_token_fails_closed(client, app):
    user_id = _user(app)
    credential_id, raw_token = _issue(app, user_id)
    with app.app_context():
        credential = db.session.get(ApiCredential, credential_id)
        credential.expires_at = _utcnow() - timedelta(seconds=1)
        db.session.commit()

    response = client.get("/api/v1/account", headers={"Authorization": f"Bearer {raw_token}"})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_token"
