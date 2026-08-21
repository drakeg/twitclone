"""Environment-backed configuration for TwitClone."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _database_uri() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        configured = configured.strip()
        if configured.startswith("postgres://"):
            return configured.replace("postgres://", "postgresql+psycopg://", 1)
        if configured.startswith("postgresql://"):
            return configured.replace("postgresql://", "postgresql+psycopg://", 1)
        return configured
    return f"sqlite:///{BASE_DIR / 'twitter_clone.db'}"


class Config:
    """Base configuration shared by all environments."""

    ENVIRONMENT = os.getenv("TWITCLONE_ENV", "development").strip().lower()
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "static" / "uploads"))
    MEDIA_STORAGE_BACKEND = os.getenv("MEDIA_STORAGE_BACKEND", "filesystem").strip().lower()
    MEDIA_S3_BUCKET = os.getenv("MEDIA_S3_BUCKET")
    MEDIA_S3_REGION = os.getenv("MEDIA_S3_REGION")
    MEDIA_S3_ENDPOINT_URL = os.getenv("MEDIA_S3_ENDPOINT_URL")
    MEDIA_S3_PREFIX = os.getenv("MEDIA_S3_PREFIX", "media").strip("/")
    SCHEDULER_ENABLED = _as_bool(os.getenv("SCHEDULER_ENABLED"), default=True)
    SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    TESTING = ENVIRONMENT == "testing"

    PASSWORD_RESET_MAX_AGE_SECONDS = int(os.getenv("PASSWORD_RESET_MAX_AGE_SECONDS", "3600"))
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = _as_bool(os.getenv("MAIL_USE_TLS"), default=False)
    MAIL_USE_SSL = _as_bool(os.getenv("MAIL_USE_SSL"), default=False)
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@ripple.local")
    MAIL_TIMEOUT_SECONDS = int(os.getenv("MAIL_TIMEOUT_SECONDS", "10"))
    MAIL_SUPPRESS_SEND = _as_bool(os.getenv("MAIL_SUPPRESS_SEND"), default=ENVIRONMENT != "production")

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_BILLING_ENABLED = _as_bool(os.getenv("STRIPE_BILLING_ENABLED"), default=False)

    @classmethod
    def validate(cls) -> None:
        """Fail clearly when required configuration is unsafe or incomplete."""
        if not cls.SECRET_KEY:
            raise RuntimeError("SECRET_KEY is required for every TwitClone environment. Set it outside source control before starting the application.")
        if cls.SCHEDULER_INTERVAL_SECONDS < 1:
            raise RuntimeError("SCHEDULER_INTERVAL_SECONDS must be at least 1")
        if cls.PASSWORD_RESET_MAX_AGE_SECONDS < 60:
            raise RuntimeError("PASSWORD_RESET_MAX_AGE_SECONDS must be at least 60")
        if cls.MAIL_USE_TLS and cls.MAIL_USE_SSL:
            raise RuntimeError("MAIL_USE_TLS and MAIL_USE_SSL cannot both be enabled")
        if cls.STRIPE_BILLING_ENABLED and (not cls.STRIPE_SECRET_KEY or not cls.STRIPE_WEBHOOK_SECRET):
            raise RuntimeError("STRIPE_BILLING_ENABLED requires STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET")
        if cls.MEDIA_STORAGE_BACKEND not in {"filesystem", "s3"}:
            raise RuntimeError("MEDIA_STORAGE_BACKEND must be filesystem or s3")
        if cls.MEDIA_STORAGE_BACKEND == "s3" and (not cls.MEDIA_S3_BUCKET or not cls.MEDIA_S3_REGION):
            raise RuntimeError("S3 media storage requires MEDIA_S3_BUCKET and MEDIA_S3_REGION")
        if cls.ENVIRONMENT == "production" and cls.MEDIA_STORAGE_BACKEND != "s3":
            raise RuntimeError("Production requires MEDIA_STORAGE_BACKEND=s3")
        if cls.ENVIRONMENT == "production" and cls.SQLALCHEMY_DATABASE_URI.startswith("sqlite:"):
            raise RuntimeError("Production requires PostgreSQL. Set DATABASE_URL to a PostgreSQL connection URL before starting TwitClone.")
        if cls.ENVIRONMENT == "production" and cls.MAIL_SUPPRESS_SEND:
            raise RuntimeError("Production account recovery requires MAIL_SUPPRESS_SEND=false")


Config.validate()
