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
        return configured
    return f"sqlite:///{BASE_DIR / 'twitter_clone.db'}"


class Config:
    """Base configuration shared by all environments."""

    ENVIRONMENT = os.getenv("TWITCLONE_ENV", "development").strip().lower()
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "static" / "uploads"))
    SCHEDULER_ENABLED = _as_bool(os.getenv("SCHEDULER_ENABLED"), default=True)
    SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    TESTING = ENVIRONMENT == "testing"

    @classmethod
    def validate(cls) -> None:
        """Fail clearly when required configuration is unsafe or incomplete."""

        if not cls.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY is required for every TwitClone environment. "
                "Set it outside source control before starting the application."
            )

        if cls.SCHEDULER_INTERVAL_SECONDS < 1:
            raise RuntimeError("SCHEDULER_INTERVAL_SECONDS must be at least 1")


Config.validate()
