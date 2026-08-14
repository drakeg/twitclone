"""Focused tests for the messaging Blueprint."""

import pytest

from flask import url_for

from twitclone.extensions import db
from twitclone.messaging.routes import messages, reply_message
from twitclone.models import DirectMessage, Notification, User


def create_message_users(app):
    with app.app_context():
        sender = User(username="alice", email="alice@example.com", password="hash")
        receiver = User(username="bob", email="bob@example.com", password="hash")
        db.session.add_all([sender, receiver])
        db.session.commit()
        original = DirectMessage(
            content="hello bob", sender_id=sender.id, receiver_id=receiver.id
        )
        db.session.add(original)
        db.session.commit()
        return sender.id, receiver.id, original.id


def log_in(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_messaging_blueprint_owns_existing_routes(app):
    assert "messaging" in app.blueprints
    assert app.view_functions["messages"] is messages
    assert app.view_functions["reply_message"] is reply_message

    with app.test_request_context():
        assert url_for("messages") == "/messages"
        assert url_for("reply_message", message_id=1) == "/reply/1"


def test_inbox_renders_received_messages(client, app):
    _, receiver_id, _ = create_message_users(app)
    log_in(client, receiver_id)

    response = client.get("/messages")

    assert response.status_code == 200
    assert b"hello bob" in response.data


def test_reply_creates_message_and_notification(client, app):
    sender_id, receiver_id, message_id = create_message_users(app)
    log_in(client, receiver_id)

    response = client.post(f"/reply/{message_id}", data={"content": "hello alice"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/messages"
    with app.app_context():
        reply = DirectMessage.query.filter_by(
            content="hello alice", sender_id=receiver_id, receiver_id=sender_id
        ).one()
        assert reply
        notification = Notification.query.filter_by(user_id=sender_id).one()
        assert notification.message == "bob replied to your message"


def test_overlength_reply_preserves_redirect_without_writes(client, app):
    sender_id, receiver_id, message_id = create_message_users(app)
    log_in(client, receiver_id)

    response = client.post(f"/reply/{message_id}", data={"content": "x" * 501})

    assert response.status_code == 302
    assert response.headers["Location"] == "/messages"
    with app.app_context():
        assert DirectMessage.query.count() == 1
        assert Notification.query.filter_by(user_id=sender_id).count() == 0


@pytest.mark.parametrize("data", [{}, {"content": ""}, {"content": "   \t"}])
def test_missing_or_blank_reply_redirects_without_writes(client, app, data):
    sender_id, receiver_id, message_id = create_message_users(app)
    log_in(client, receiver_id)

    response = client.post(f"/reply/{message_id}", data=data)

    assert response.status_code == 302
    assert response.headers["Location"] == "/messages"
    with app.app_context():
        assert DirectMessage.query.count() == 1
        assert Notification.query.filter_by(user_id=sender_id).count() == 0


@pytest.mark.parametrize("method", ["get", "post"])
def test_only_recipient_can_access_reply(client, app, method):
    sender_id, _, message_id = create_message_users(app)
    log_in(client, sender_id)

    response = getattr(client, method)(
        f"/reply/{message_id}", data={"content": "unauthorized reply"}
    )

    assert response.status_code == 404
    with app.app_context():
        assert DirectMessage.query.count() == 1
        assert Notification.query.count() == 0


def test_exactly_500_character_reply_is_accepted(client, app):
    sender_id, receiver_id, message_id = create_message_users(app)
    log_in(client, receiver_id)

    response = client.post(f"/reply/{message_id}", data={"content": "x" * 500})

    assert response.status_code == 302
    with app.app_context():
        reply = DirectMessage.query.filter_by(sender_id=receiver_id).one()
        assert len(reply.content) == 500
        assert Notification.query.filter_by(user_id=sender_id, read=False).count() == 1


def test_reply_form_exposes_matching_browser_constraints(client, app):
    _, receiver_id, message_id = create_message_users(app)
    log_in(client, receiver_id)

    response = client.get(f"/reply/{message_id}")

    assert response.status_code == 200
    assert b'name="content"' in response.data
    assert b'maxlength="500"' in response.data
    assert b"required" in response.data


def test_messaging_routes_still_require_login(client):
    assert client.get("/messages").headers["Location"].startswith("/login?")
    assert client.get("/reply/1").headers["Location"].startswith("/login?")
