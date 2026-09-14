"""First-party API credential persistence and bearer authentication."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from twitclone.extensions import db

SUPPORTED_API_SCOPES = {"posts:read", "posts:write"}
DEFAULT_CREDENTIAL_LIFETIME_DAYS = 90
MAX_CREDENTIAL_LIFETIME_DAYS = 365


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ApiCredential(db.Model):
    __tablename__ = "api_credential"
    __table_args__ = (
        db.UniqueConstraint("token_digest", name="uq_api_credential_token_digest"),
        db.CheckConstraint("length(label) between 1 and 80", name="ck_api_credential_label_length"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    label = db.Column(db.String(80), nullable=False)
    token_prefix = db.Column(db.String(16), nullable=False)
    token_digest = db.Column(db.String(64), nullable=False)
    scopes = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")

    @property
    def scope_set(self):
        return {value for value in self.scopes.split(" ") if value}

    def is_active_at(self, now):
        return self.revoked_at is None and self.expires_at > now


def issue_api_credential(*, user_id, label, scopes, expires_at=None):
    clean_label = (label or "").strip()
    requested_scopes = set(scopes or [])
    if not clean_label or len(clean_label) > 80:
        raise ValueError("Credential label must be between 1 and 80 characters.")
    if not requested_scopes or not requested_scopes.issubset(SUPPORTED_API_SCOPES):
        raise ValueError("Credential scopes must be a non-empty supported scope set.")

    now = _utcnow()
    expires_at = expires_at or now + timedelta(days=DEFAULT_CREDENTIAL_LIFETIME_DAYS)
    if expires_at <= now:
        raise ValueError("Credential expiration must be in the future.")
    if expires_at > now + timedelta(days=MAX_CREDENTIAL_LIFETIME_DAYS):
        raise ValueError("Credential expiration cannot exceed 365 days.")

    raw_token = f"rpl_{secrets.token_urlsafe(32)}"
    credential = ApiCredential(
        user_id=user_id,
        label=clean_label,
        token_prefix=raw_token[:12],
        token_digest=_token_digest(raw_token),
        scopes=" ".join(sorted(requested_scopes)),
        expires_at=expires_at,
    )
    db.session.add(credential)
    db.session.flush()
    return credential, raw_token


def authenticate_bearer_token(raw_token, *, required_scope=None, now=None):
    if not raw_token or not raw_token.startswith("rpl_"):
        return None
    now = now or _utcnow()
    credential = ApiCredential.query.filter_by(token_digest=_token_digest(raw_token)).first()
    if credential is None or not credential.is_active_at(now):
        return None
    if required_scope and required_scope not in credential.scope_set:
        return None
    credential.last_used_at = now
    db.session.commit()
    return credential


def revoke_api_credential(credential, *, now=None):
    if credential.revoked_at is None:
        credential.revoked_at = now or _utcnow()
        db.session.commit()
    return credential


__all__ = [
    "ApiCredential",
    "DEFAULT_CREDENTIAL_LIFETIME_DAYS",
    "MAX_CREDENTIAL_LIFETIME_DAYS",
    "SUPPORTED_API_SCOPES",
    "authenticate_bearer_token",
    "issue_api_credential",
    "revoke_api_credential",
]
