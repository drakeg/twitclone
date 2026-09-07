"""Sprint 15 Story 15.1 creator-support foundation coverage."""

from twitclone.creator_support import CreatorSupportProfile
from twitclone.extensions import db
from twitclone.models import Entitlement, User


def _creator(app):
    with app.app_context():
        user = User(username="support_creator", email="support@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_creator_support_settings_require_authentication(client):
    response = client.get("/creator/support")
    assert response.status_code in (302, 401)


def test_creator_can_publish_informational_support_page(client, app):
    user_id = _creator(app)
    _login(client, user_id)

    response = client.post(
        "/creator/support",
        data={"enabled": "1", "message": "Help me keep making detailed RV travel guides."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Creator support profile updated" in response.data

    public = client.get("/support/support_creator")
    assert public.status_code == 200
    assert b"Help me keep making detailed RV travel guides" in public.data
    assert b"No payment is processed on this page yet" in public.data

    with app.app_context():
        profile = CreatorSupportProfile.query.filter_by(user_id=user_id).one()
        assert profile.enabled is True
        assert Entitlement.query.filter_by(user_id=user_id).count() == 0


def test_enabled_support_requires_message(client, app):
    user_id = _creator(app)
    _login(client, user_id)

    response = client.post(
        "/creator/support",
        data={"enabled": "1", "message": "   "},
    )
    assert response.status_code == 200
    assert b"Add a short support message" in response.data

    with app.app_context():
        assert CreatorSupportProfile.query.filter_by(user_id=user_id).first() is None


def test_creator_can_disable_support_page_without_deleting_profile(client, app):
    user_id = _creator(app)
    with app.app_context():
        db.session.add(CreatorSupportProfile(user_id=user_id, enabled=True, message="Existing support message"))
        db.session.commit()
    _login(client, user_id)

    response = client.post(
        "/creator/support",
        data={"message": "Existing support message"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    hidden = client.get("/support/support_creator")
    assert hidden.status_code == 404

    with app.app_context():
        profile = CreatorSupportProfile.query.filter_by(user_id=user_id).one()
        assert profile.enabled is False
        assert profile.message == "Existing support message"


def test_support_message_is_bounded_to_persisted_contract(client, app):
    user_id = _creator(app)
    _login(client, user_id)
    oversized = "x" * 400

    response = client.post("/creator/support", data={"enabled": "1", "message": oversized})
    assert response.status_code == 302

    with app.app_context():
        profile = CreatorSupportProfile.query.filter_by(user_id=user_id).one()
        assert len(profile.message) == 280
