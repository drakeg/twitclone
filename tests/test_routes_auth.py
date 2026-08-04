"""Focused tests for the authentication Blueprint."""

from flask import url_for

from twitclone.auth.routes import login, logout, register
from twitclone.extensions import bcrypt, db
from twitclone.models import User


def test_auth_blueprint_owns_legacy_routes(app):
    assert "auth" in app.blueprints
    assert app.view_functions["login"] is login
    assert app.view_functions["logout"] is logout
    assert app.view_functions["register"] is register

    with app.test_request_context():
        assert url_for("login") == "/login"
        assert url_for("logout") == "/logout"
        assert url_for("register") == "/register"


def test_registration_hashes_password_and_preserves_redirect(client, app):
    response = client.post(
        "/register",
        data={"username": "alice", "email": "alice@example.com", "password": "secret"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").one()
        assert user.password != "secret"
        assert bcrypt.check_password_hash(user.password, "secret")


def test_login_and_logout_preserve_redirects(client, app):
    with app.app_context():
        user = User(
            username="alice",
            email="alice@example.com",
            password=bcrypt.generate_password_hash("secret").decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()

    login_response = client.post(
        "/login", data={"email": "alice@example.com", "password": "secret"}
    )
    assert login_response.status_code == 302
    assert login_response.headers["Location"] == "/"

    logout_response = client.get("/logout")
    assert logout_response.status_code == 302
    assert logout_response.headers["Location"] == "/login"


def test_invalid_login_renders_existing_template(client):
    response = client.post(
        "/login", data={"email": "missing@example.com", "password": "wrong"}
    )

    assert response.status_code == 200
    assert b"Login Unsuccessful" in response.data
