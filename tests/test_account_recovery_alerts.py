"""Regression coverage for account recovery and unread navigation alerts."""

from twitclone.auth.recovery import generate_reset_token
from twitclone.extensions import bcrypt, db
from twitclone.models import DirectMessage, Notification, User


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


def test_notification_inbox_does_not_clear_unread_message_badge(client, app):
    user_id = _create_user(app)
    sender_id = _create_user(app, username="bob", email="bob@example.com")
    with app.app_context():
        db.session.add_all(
            [
                DirectMessage(
                    sender_id=sender_id,
                    receiver_id=user_id,
                    content="hello alice",
                ),
                Notification(user_id=user_id, message="bob sent you a message"),
                Notification(user_id=user_id, message="carol followed you"),
            ]
        )
        db.session.commit()
    _login(client, user_id)

    home = client.get("/")
    assert b"2 unread notifications" in home.data
    assert b"1 unread messages" in home.data

    notifications = client.get("/notifications")
    assert notifications.status_code == 200

    home_after_notifications = client.get("/")
    assert b"unread notifications" not in home_after_notifications.data
    assert b"1 unread messages" in home_after_notifications.data
    with app.app_context():
        message = DirectMessage.query.filter_by(receiver_id=user_id).one()
        assert message.read is False

    messages = client.get("/messages")
    assert messages.status_code == 200
    with app.app_context():
        message = DirectMessage.query.filter_by(receiver_id=user_id).one()
        assert message.read is True

    home_after_messages = client.get("/")
    assert b"unread messages" not in home_after_messages.data


def test_opening_messages_does_not_clear_other_notifications(client, app):
    user_id = _create_user(app)
    sender_id = _create_user(app, username="bob", email="bob@example.com")
    with app.app_context():
        db.session.add_all(
            [
                DirectMessage(
                    sender_id=sender_id,
                    receiver_id=user_id,
                    content="hello alice",
                ),
                Notification(user_id=user_id, message="bob sent you a message"),
                Notification(user_id=user_id, message="carol followed you"),
            ]
        )
        db.session.commit()
    _login(client, user_id)

    response = client.get("/messages")
    assert response.status_code == 200

    home = client.get("/")
    assert b"2 unread notifications" in home.data
    assert b"unread messages" not in home.data
    with app.app_context():
        assert DirectMessage.query.filter_by(receiver_id=user_id, read=False).count() == 0
        assert Notification.query.filter_by(user_id=user_id, read=False).count() == 2
