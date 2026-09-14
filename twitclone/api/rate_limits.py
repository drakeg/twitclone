"""Database-backed fixed-window rate limiting for the public API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac

from sqlalchemy.exc import IntegrityError

from twitclone.extensions import db

DEFAULT_WINDOW_SECONDS = 60
DEFAULT_PUBLIC_READ_LIMIT = 60
DEFAULT_INVALID_TOKEN_LIMIT = 20
DEFAULT_CREDENTIAL_LIMIT = 120


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _window_start(now, window_seconds):
    timestamp = int(now.replace(tzinfo=UTC).timestamp())
    bucket_timestamp = timestamp - (timestamp % window_seconds)
    return datetime.fromtimestamp(bucket_timestamp, UTC).replace(tzinfo=None)


def hash_rate_limit_subject(subject, *, secret_key):
    """Hash a client identifier so raw IP addresses/tokens are never persisted."""
    key = str(secret_key or "").encode("utf-8")
    return hmac.new(key, str(subject).encode("utf-8"), hashlib.sha256).hexdigest()


class ApiRateLimitBucket(db.Model):
    __tablename__ = "api_rate_limit_bucket"
    __table_args__ = (
        db.UniqueConstraint(
            "bucket_type",
            "subject_hash",
            "window_started_at",
            name="uq_api_rate_limit_bucket_window",
        ),
        db.CheckConstraint("request_count >= 1", name="ck_api_rate_limit_request_count"),
    )

    id = db.Column(db.Integer, primary_key=True)
    bucket_type = db.Column(db.String(40), nullable=False)
    subject_hash = db.Column(db.String(64), nullable=False)
    window_started_at = db.Column(db.DateTime, nullable=False)
    window_expires_at = db.Column(db.DateTime, nullable=False, index=True)
    request_count = db.Column(db.Integer, nullable=False, default=1)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: int


def consume_rate_limit(
    *,
    bucket_type,
    subject,
    secret_key,
    limit,
    window_seconds=DEFAULT_WINDOW_SECONDS,
    now=None,
):
    """Consume one request from a fixed window shared through the database."""
    if limit < 1:
        raise ValueError("Rate limit must be at least 1.")
    if window_seconds < 1:
        raise ValueError("Rate-limit window must be at least 1 second.")

    now = now or _utcnow()
    window_started_at = _window_start(now, window_seconds)
    reset_at = window_started_at + timedelta(seconds=window_seconds)
    subject_hash = hash_rate_limit_subject(subject, secret_key=secret_key)

    bucket = ApiRateLimitBucket.query.filter_by(
        bucket_type=bucket_type,
        subject_hash=subject_hash,
        window_started_at=window_started_at,
    ).first()

    if bucket is None:
        db.session.query(ApiRateLimitBucket).filter(
            ApiRateLimitBucket.window_expires_at < window_started_at
        ).delete(synchronize_session=False)
        bucket = ApiRateLimitBucket(
            bucket_type=bucket_type,
            subject_hash=subject_hash,
            window_started_at=window_started_at,
            window_expires_at=reset_at,
            request_count=1,
        )
        db.session.add(bucket)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            bucket = ApiRateLimitBucket.query.filter_by(
                bucket_type=bucket_type,
                subject_hash=subject_hash,
                window_started_at=window_started_at,
            ).one()
        else:
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=max(limit - 1, 0),
                reset_at=reset_at,
                retry_after=max(int((reset_at - now).total_seconds()), 1),
            )

    if bucket.request_count >= limit:
        return RateLimitResult(
            allowed=False,
            limit=limit,
            remaining=0,
            reset_at=reset_at,
            retry_after=max(int((reset_at - now).total_seconds()), 1),
        )

    bucket.request_count += 1
    db.session.commit()
    return RateLimitResult(
        allowed=True,
        limit=limit,
        remaining=max(limit - bucket.request_count, 0),
        reset_at=reset_at,
        retry_after=max(int((reset_at - now).total_seconds()), 1),
    )


__all__ = [
    "ApiRateLimitBucket",
    "DEFAULT_CREDENTIAL_LIMIT",
    "DEFAULT_INVALID_TOKEN_LIMIT",
    "DEFAULT_PUBLIC_READ_LIMIT",
    "DEFAULT_WINDOW_SECONDS",
    "RateLimitResult",
    "consume_rate_limit",
    "hash_rate_limit_subject",
]
