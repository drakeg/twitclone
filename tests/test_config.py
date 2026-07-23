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
        "SCHEDULER_ENABLED",
        "SCHEDULER_INTERVAL_SECONDS",
    }
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

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
