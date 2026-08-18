"""Regression coverage for account recovery and unread navigation alerts."""

from twitclone.auth.recovery import generate_reset_token
from twitclone.extensions import bcrypt, db
from twitclone.models import Notification, User


def _create_user(app, username="alice", email="alice@example.com", password="old-password"):
    with app.app_context():
        user = User(
            username=username,
            email=email,
            password=bcrypt.generate_password_hash(password).decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_login_links_to_account_recovery(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Forgot username or password?" in response.data
    assert b"/forgot-account" in response.data


def test_recovery_request_does_not_disclose_account_existence(client, app):
    _create_user(app)
    known = client.post("/forgot-account", data={"email": "alice@example.com"}, follow_redirects=True)
    missing = client.post("/forgot-account", data={"email": "missing@example.com"}, follow_redirects=True)
    expected = b"If that email belongs to a Ripple account, recovery instructions have been sent."
    assert expected in known.data
    assert expected in missing.data


def test_valid_reset_token_changes_password(client, app):
    _create_user(app)
    with app.app_context():
        token = generate_reset_token("alice@example.com")

    response = client.post(
        f"/reset-password/{token}",
        data={"password": "new-password", "password_confirm": "new-password"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").one()
        assert bcrypt.check_password_hash(user.password, "new-password")


def test_nav_shows_unread_counts_and_messages_clear_only_message_alerts(client, app):
    user_id = _create_user(app)
    with app.app_context():
        db.session.add_all(
            [
                Notification(user_id=user_id, message="bob sent you a message"),
                Notification(user_id=user_id, message="carol followed you"),
            ]
        )
        db.session.commit()
    _login(client, user_id)

    home = client.get("/")
    assert b"2 unread notifications" in home.data
    assert b"1 unread messages" in home.data

    messages = client.get("/messages")
    assert messages.status_code == 200
    with app.app_context():
        message_notice = Notification.query.filter_by(message="bob sent you a message").one()
        follow_notice = Notification.query.filter_by(message="carol followed you").one()
        assert message_notice.read is True
        assert follow_notice.read is False

    home_after = client.get("/")
    assert b"1 unread notifications" in home_after.data
    assert b"unread messages" not in home_after.data
