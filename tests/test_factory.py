"""Smoke tests for the TwitClone application factory."""

from application import application
from twitclone import create_app


def test_factory_returns_configured_application():
    created = create_app()

    assert created is application
    assert created.config["SECRET_KEY"]
    assert created.config["SQLALCHEMY_DATABASE_URI"]


def test_factory_preserves_registered_routes():
    created = create_app()
    rules = {rule.rule for rule in created.url_map.iter_rules()}

    assert "/" in rules
    assert "/login" in rules
    assert "/register" in rules
