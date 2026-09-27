"""Shared pytest fixtures for an isolated TwitClone test environment."""

import os

import pytest


# These values must be set before importing the configured application because
# Flask-SQLAlchemy reads the database URI when its engine is first accessed.
os.environ.setdefault("TWITCLONE_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("UPLOAD_FOLDER", "/tmp/twitclone-test-uploads")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("SCHEDULER_INTERVAL_SECONDS", "60")

from application import application  # noqa: E402
from app import db, scheduler  # noqa: E402
from twitclone.api.rate_limits import (  # noqa: E402
    DEFAULT_CREDENTIAL_LIMIT,
    DEFAULT_INVALID_TOKEN_LIMIT,
    DEFAULT_PUBLIC_READ_LIMIT,
    DEFAULT_WINDOW_SECONDS,
)


@pytest.fixture()
def app():
    """Provide an application backed by an isolated in-memory database."""
    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SCHEDULER_ENABLED=False,
        API_CREDENTIAL_LIMIT=DEFAULT_CREDENTIAL_LIMIT,
        API_INVALID_TOKEN_LIMIT=DEFAULT_INVALID_TOKEN_LIMIT,
        API_PUBLIC_READ_LIMIT=DEFAULT_PUBLIC_READ_LIMIT,
        API_RATE_LIMIT_WINDOW_SECONDS=DEFAULT_WINDOW_SECONDS,
    )

    if scheduler.running:
        scheduler.shutdown(wait=False)

    with application.app_context():
        db.drop_all()
        db.create_all()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Return Flask's test client for the isolated application."""
    return app.test_client()
