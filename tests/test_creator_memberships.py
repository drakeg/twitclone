"""Sprint 15 Story 15.3 membership-offering coverage."""

from twitclone.creator_memberships import CreatorMembershipOffering
from twitclone.creator_support import CreatorSupportProfile
from twitclone.extensions import db
from twitclone.models import Entitlement, User


def _creator(app):
    with app.app_context():
        user = User(username="membership_creator", email="membership@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _publish_support(app, user_id):
    with app.app_context():
        db.session.add(
            CreatorSupportProfile(
                user_id=user_id,
                enabled=True,
                message="Support my creator work.",
            )
        )
        db.session.commit()


def test_membership_settings_require_authentication(client):
    response = client.get("/creator/membership")
    assert response.status_code in (302, 401)


def test_creator_can_publish_membership_offering_without_enrollment_or_entitlement(client, app):
    user_id = _creator(app)
    _publish_support(app, user_id)
    _login(client, user_id)

    response = client.post(
        "/creator/membership",
        data={
            "enabled": "1",
            "name": "Road Notes Club",
            "description": "Extra trip notes and creator Q&A for future supporters.",
            "benefits": ["supporter_updates", "member_q_and_a"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Membership offering updated" in response.data

    public = client.get("/support/membership_creator/membership")
    assert public.status_code == 200
    assert b"Road Notes Club" in public.data
    assert b"Supporter-only creator updates" in public.data
    assert b"Member Q&amp;A participation" in public.data
    assert b"Enrollment and payment are not enabled yet" in public.data

    with app.app_context():
        offering = CreatorMembershipOffering.query.filter_by(user_id=user_id).one()
        assert offering.enabled is True
        assert offering.benefit_keys == ["supporter_updates", "member_q_and_a"]
        assert Entitlement.query.filter_by(user_id=user_id).count() == 0


def test_enabled_membership_requires_name_description_and_supported_benefit(client, app):
    user_id = _creator(app)
    _login(client, user_id)

    missing_name = client.post(
        "/creator/membership",
        data={"enabled": "1", "description": "Description", "benefits": ["supporter_updates"]},
    )
    assert missing_name.status_code == 200
    assert b"Add a membership name" in missing_name.data

    missing_description = client.post(
        "/creator/membership",
        data={"enabled": "1", "name": "Club", "benefits": ["supporter_updates"]},
    )
    assert missing_description.status_code == 200
    assert b"Add a membership description" in missing_description.data

    unsupported_only = client.post(
        "/creator/membership",
        data={"enabled": "1", "name": "Club", "description": "Description", "benefits": ["buy_reach"]},
    )
    assert unsupported_only.status_code == 200
    assert b"Choose at least one supported membership benefit" in unsupported_only.data

    with app.app_context():
        assert CreatorMembershipOffering.query.filter_by(user_id=user_id).first() is None


def test_membership_public_page_requires_published_support_and_offering(client, app):
    user_id = _creator(app)
    with app.app_context():
        db.session.add(
            CreatorMembershipOffering(
                user_id=user_id,
                enabled=True,
                name="Hidden Club",
                description="Not public without support profile.",
                benefits="early_access",
            )
        )
        db.session.commit()

    assert client.get("/support/membership_creator/membership").status_code == 404

    _publish_support(app, user_id)
    with app.app_context():
        offering = CreatorMembershipOffering.query.filter_by(user_id=user_id).one()
        offering.enabled = False
        db.session.commit()

    assert client.get("/support/membership_creator/membership").status_code == 404


def test_creator_can_disable_membership_without_deleting_configuration(client, app):
    user_id = _creator(app)
    _publish_support(app, user_id)
    with app.app_context():
        db.session.add(
            CreatorMembershipOffering(
                user_id=user_id,
                enabled=True,
                name="Reversible Club",
                description="Saved configuration.",
                benefits="downloadable_resources",
            )
        )
        db.session.commit()
    _login(client, user_id)

    response = client.post(
        "/creator/membership",
        data={
            "name": "Reversible Club",
            "description": "Saved configuration.",
            "benefits": ["downloadable_resources"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert client.get("/support/membership_creator/membership").status_code == 404

    with app.app_context():
        offering = CreatorMembershipOffering.query.filter_by(user_id=user_id).one()
        assert offering.enabled is False
        assert offering.name == "Reversible Club"
        assert offering.benefit_keys == ["downloadable_resources"]
