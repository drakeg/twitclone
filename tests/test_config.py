"""Tests for environment-backed configuration."""

import importlib
import sys

import pytest


def load_config(monkeypatch, **environment):
    keys = {
        "TWITCLONE_ENV",
        "SECRET_KEY",
        "DATABASE_URL",
        "UPLOAD_FOLDER",
        "MEDIA_STORAGE_BACKEND",
        "MEDIA_S3_BUCKET",
        "MEDIA_S3_REGION",
        "MEDIA_S3_ENDPOINT_URL",
        "MEDIA_S3_PREFIX",
        "SCHEDULER_ENABLED",
        "SCHEDULER_INTERVAL_SECONDS",
    }
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    if environment.get("TWITCLONE_ENV") == "production":
        monkeypatch.setenv("MEDIA_STORAGE_BACKEND", environment.get("MEDIA_STORAGE_BACKEND", "s3"))
        monkeypatch.setenv("MEDIA_S3_BUCKET", environment.get("MEDIA_S3_BUCKET", "ripple-media"))
        monkeypatch.setenv("MEDIA_S3_REGION", environment.get("MEDIA_S3_REGION", "nyc3"))

    sys.modules.pop("config", None)
    return importlib.import_module("config")


def test_secret_key_is_required_in_development(monkeypatch):
    with pytest.raises(RuntimeError, match="SECRET_KEY is required"):
        load_config(monkeypatch, TWITCLONE_ENV="development")


def test_secret_key_is_required_in_testing(monkeypatch):
    with pytest.raises(RuntimeError, match="SECRET_KEY is required"):
        load_config(monkeypatch, TWITCLONE_ENV="testing")


def test_secret_key_is_required_in_production(monkeypatch):
    with pytest.raises(RuntimeError, match="SECRET_KEY is required"):
        load_config(monkeypatch, TWITCLONE_ENV="production")


def test_environment_values_override_defaults(monkeypatch, tmp_path):
    upload_folder = tmp_path / "uploads"
    config = load_config(
        monkeypatch,
        TWITCLONE_ENV="testing",
        SECRET_KEY="test-only-secret-not-for-production",
        DATABASE_URL="sqlite:///:memory:",
        UPLOAD_FOLDER=str(upload_folder),
        SCHEDULER_ENABLED="false",
        SCHEDULER_INTERVAL_SECONDS="15",
    )

    assert config.Config.TESTING is True
    assert config.Config.SECRET_KEY == "test-only-secret-not-for-production"
    assert config.Config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"
    assert config.Config.UPLOAD_FOLDER == str(upload_folder)
    assert config.Config.SCHEDULER_ENABLED is False
    assert config.Config.SCHEDULER_INTERVAL_SECONDS == 15


def test_scheduler_interval_must_be_positive(monkeypatch):
    with pytest.raises(RuntimeError, match="must be at least 1"):
        load_config(
            monkeypatch,
            SECRET_KEY="test-only-secret-not-for-production",
            SCHEDULER_INTERVAL_SECONDS="0",
        )


def test_s3_media_storage_requires_bucket_and_region(monkeypatch):
    with pytest.raises(RuntimeError, match="requires MEDIA_S3_BUCKET and MEDIA_S3_REGION"):
        load_config(monkeypatch, TWITCLONE_ENV="testing", SECRET_KEY="test-only-secret", DATABASE_URL="sqlite:///:memory:", MEDIA_STORAGE_BACKEND="s3")


def test_production_rejects_filesystem_media_storage(monkeypatch):
    with pytest.raises(RuntimeError, match="Production requires MEDIA_STORAGE_BACKEND=s3"):
        load_config(monkeypatch, TWITCLONE_ENV="production", SECRET_KEY="test-only-secret", DATABASE_URL="postgresql://user:password@database.example/ripple", MEDIA_STORAGE_BACKEND="filesystem")


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (
            "postgres://user:password@database.example/twitclone",
            "postgresql+psycopg://user:password@database.example/twitclone",
        ),
        (
            "postgresql://user:password@database.example/twitclone",
            "postgresql+psycopg://user:password@database.example/twitclone",
        ),
        (
            "postgresql+psycopg://user:password@database.example/twitclone",
            "postgresql+psycopg://user:password@database.example/twitclone",
        ),
    ],
)
def test_postgresql_urls_use_the_supported_psycopg_driver(
    monkeypatch, configured, expected
):
    config = load_config(
        monkeypatch,
        TWITCLONE_ENV="production",
        SECRET_KEY="test-only-secret-not-for-production",
        DATABASE_URL=configured,
    )

    assert config.Config.SQLALCHEMY_DATABASE_URI == expected


@pytest.mark.parametrize("database_url", [None, "sqlite:////data/twitclone.db"])
def test_sqlite_is_rejected_in_production(monkeypatch, database_url):
    environment = {
        "TWITCLONE_ENV": "production",
        "SECRET_KEY": "test-only-secret-not-for-production",
    }
    if database_url:
        environment["DATABASE_URL"] = database_url

    with pytest.raises(RuntimeError, match="Production requires PostgreSQL"):
        load_config(monkeypatch, **environment)
