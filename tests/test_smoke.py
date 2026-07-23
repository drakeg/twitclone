"""Baseline smoke tests for configured TwitClone startup and public access."""

from app import scheduler


def test_application_uses_testing_configuration(app):
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    assert app.config["SCHEDULER_ENABLED"] is False
    assert scheduler.running is False


def test_public_homepage_responds(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


def test_login_page_responds(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
