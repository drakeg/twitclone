"""Sprint 26 Story 26.3 membership administration audit coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import (
    Space,
    SpaceMembership,
    SpaceMembershipAction,
    SpaceModerationAction,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="audit_owner", email="audit-owner@example.com", password="hash")
        moderator = User(username="audit_moderator", email="audit-moderator@example.com", password="hash")
        member = User(username="audit_member", email="audit-member@example.com", password="hash")
        db.session.add_all([owner, moderator, member])
        db.session.flush()

        space = Space(
            slug="membership-audit",
            name="Membership Audit",
            description="Dedicated membership administration history.",
            owner_id=owner.id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=moderator.id, role="moderator"),
            SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
        ])
        db.session.commit()
        return {
            "space": space.id,
            "owner": owner.id,
            "moderator": moderator.id,
            "member": member.id,
        }


def test_role_change_uses_membership_audit_not_content_moderation(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    response = client.post(
        f"/spaces/membership-audit/members/{ids['member']}/role",
        data={"role": "moderator"},
    )
    assert response.status_code == 302

    with app.app_context():
        action = SpaceMembershipAction.query.filter_by(
            space_id=ids["space"],
            affected_user_id=ids["member"],
            action_type="role_changed",
        ).one()
        assert action.actor_id == ids["owner"]
        assert action.previous_role == "member"
        assert action.new_role == "moderator"
        assert SpaceModerationAction.query.filter_by(
            space_id=ids["space"],
            target_type="membership",
        ).count() == 0


def test_ownership_transfer_records_previous_and_new_role(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    response = client.post(
        "/spaces/membership-audit/ownership",
        data={"user_id": ids["moderator"], "confirm": "transfer"},
    )
    assert response.status_code == 302

    with app.app_context():
        action = SpaceMembershipAction.query.filter_by(
            space_id=ids["space"],
            action_type="ownership_transferred",
        ).one()
        assert action.actor_id == ids["owner"]
        assert action.affected_user_id == ids["moderator"]
        assert action.previous_role == "moderator"
        assert action.new_role == "owner"
        space = db.session.get(Space, ids["space"])
        assert space.owner_id == ids["moderator"]


def test_member_removal_history_survives_membership_deletion(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    response = client.post(
        f"/spaces/membership-audit/members/{ids['member']}/remove",
        data={"confirm": "remove"},
    )
    assert response.status_code == 302

    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=ids["space"],
            user_id=ids["member"],
        ).first() is None
        action = SpaceMembershipAction.query.filter_by(
            space_id=ids["space"],
            affected_user_id=ids["member"],
            action_type="member_removed",
        ).one()
        assert action.previous_role == "member"
        assert action.new_role is None


def test_membership_history_is_owner_only_on_operator_dashboard(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    client.post(
        f"/spaces/membership-audit/members/{ids['member']}/role",
        data={"role": "moderator"},
    )

    owner_page = client.get("/spaces/membership-audit/operator")
    assert owner_page.status_code == 200
    assert b"Membership administration history" in owner_page.data
    assert b"Role Changed" in owner_page.data
    assert b"audit_member" in owner_page.data

    _login(client, ids["moderator"])
    moderator_page = client.get("/spaces/membership-audit/operator")
    assert moderator_page.status_code == 200
    assert b"Membership administration history" not in moderator_page.data
