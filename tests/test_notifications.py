"""Focused tests for the notifications Blueprint."""

from datetime import datetime, timedelta

from flask import url_for

from twitclone.extensions import db
from twitclone.models import Notification, User
from twitclone.notifications.routes import notifications


def create_logged_in_user(client, app):
    with app.app_context():
        user = User(username="alice", email="alice@example.com", password="hash")
        other = User(username="bob", email="bob@example.com", password="hash")
        db.session.add_all([user, other])
        db.session.commit()
        user_id = user.id
        other_id = other.id
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
    return user_id, other_id


def test_notifications_blueprint_owns_existing_route(app):
    assert "notifications" in app.blueprints
    assert app.view_functions["notifications"] is notifications

    with app.test_request_context():
        assert url_for("notifications") == "/notifications"


def test_notifications_render_for_current_user_in_newest_first_order(client, app):
    user_id, other_id = create_logged_in_user(client, app)
    now = datetime.utcnow()
    with app.app_context():
        db.session.add_all(
            [
                Notification(
                    user_id=user_id, message="older notification", timestamp=now
                ),
                Notification(
                    user_id=user_id,
                    message="newer notification",
                    timestamp=now + timedelta(minutes=1),
                ),
                Notification(
                    user_id=other_id,
                    message="another user's notification",
                    timestamp=now + timedelta(minutes=2),
                ),
            ]
        )
        db.session.commit()

    response = client.get("/notifications")

    assert response.status_code == 200
    assert b"another user's notification" not in response.data
    assert response.data.index(b"newer notification") < response.data.index(
        b"older notification"
    )


def test_notifications_still_require_login(client):
    response = client.get("/notifications")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?")
