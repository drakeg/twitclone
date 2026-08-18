"""Regression coverage for user-owned message and notification deletion."""

from twitclone.extensions import db
from twitclone.models import DirectMessage, Notification, User


def _users(app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        carol = User(username="carol", email="carol@example.com", password="hash")
        db.session.add_all([alice, bob, carol])
        db.session.commit()
        return alice.id, bob.id, carol.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_receiver_deletion_hides_message_only_from_receiver(client, app):
    alice_id, bob_id, _ = _users(app)
    with app.app_context():
        message = DirectMessage(
            content="keep for sender",
            sender_id=alice_id,
            receiver_id=bob_id,
        )
        db.session.add(message)
        db.session.commit()
        message_id = message.id

    _login(client, bob_id)
    response = client.post(f"/messages/{message_id}/delete")
    assert response.status_code == 302

    with app.app_context():
        message = db.session.get(DirectMessage, message_id)
        assert message is not None
        assert message.deleted_by_receiver is True
        assert message.deleted_by_sender is False
        assert message.read is True

    assert b"keep for sender" not in client.get("/messages").data

    _login(client, alice_id)
    assert b"keep for sender" in client.get("/messages").data


def test_message_is_physically_removed_after_both_users_delete(client, app):
    alice_id, bob_id, _ = _users(app)
    with app.app_context():
        message = DirectMessage(
            content="delete both sides",
            sender_id=alice_id,
            receiver_id=bob_id,
        )
        db.session.add(message)
        db.session.commit()
        message_id = message.id

    _login(client, alice_id)
    assert client.post(f"/messages/{message_id}/delete").status_code == 302
    with app.app_context():
        assert db.session.get(DirectMessage, message_id) is not None

    _login(client, bob_id)
    assert client.post(f"/messages/{message_id}/delete").status_code == 302
    with app.app_context():
        assert db.session.get(DirectMessage, message_id) is None


def test_unrelated_user_cannot_delete_message(client, app):
    alice_id, bob_id, carol_id = _users(app)
    with app.app_context():
        message = DirectMessage(
            content="private",
            sender_id=alice_id,
            receiver_id=bob_id,
        )
        db.session.add(message)
        db.session.commit()
        message_id = message.id

    _login(client, carol_id)
    assert client.post(f"/messages/{message_id}/delete").status_code == 404
    with app.app_context():
        assert db.session.get(DirectMessage, message_id) is not None


def test_sent_messages_are_collapsed_by_default_and_have_delete_control(client, app):
    alice_id, bob_id, _ = _users(app)
    with app.app_context():
        message = DirectMessage(
            content="sent message",
            sender_id=alice_id,
            receiver_id=bob_id,
        )
        db.session.add(message)
        db.session.commit()
        message_id = message.id

    _login(client, alice_id)
    response = client.get("/messages")

    assert response.status_code == 200
    assert b'data-bs-target="#sentMessages"' in response.data
    assert b'class="collapse mt-3" id="sentMessages"' in response.data
    assert f'/messages/{message_id}/delete'.encode() in response.data


def test_owner_can_delete_notification(client, app):
    alice_id, _, _ = _users(app)
    with app.app_context():
        notification = Notification(user_id=alice_id, message="old notification")
        db.session.add(notification)
        db.session.commit()
        notification_id = notification.id

    _login(client, alice_id)
    response = client.post(f"/notifications/{notification_id}/delete")

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Notification, notification_id) is None


def test_other_user_cannot_delete_notification(client, app):
    alice_id, bob_id, _ = _users(app)
    with app.app_context():
        notification = Notification(user_id=alice_id, message="alice only")
        db.session.add(notification)
        db.session.commit()
        notification_id = notification.id

    _login(client, bob_id)
    assert client.post(f"/notifications/{notification_id}/delete").status_code == 404
    with app.app_context():
        assert db.session.get(Notification, notification_id) is not None
