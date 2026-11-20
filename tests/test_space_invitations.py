"""Sprint 27 Story 27.1 consent-based Space invitation coverage."""

from twitclone.extensions import db
from twitclone.models import Notification, User
from twitclone.spaces.models import Space, SpaceInvitation, SpaceMembership


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="invite_owner", email="invite-owner@example.com", password="hash")
        moderator = User(username="invite_moderator", email="invite-moderator@example.com", password="hash")
        member = User(username="invite_member", email="invite-member@example.com", password="hash")
        invitee = User(username="invite_target", email="invite-target@example.com", password="hash")
        outsider = User(username="invite_outsider", email="invite-outsider@example.com", password="hash")
        db.session.add_all([owner, moderator, member, invitee, outsider])
        db.session.flush()

        space = Space(
            slug="invitation-space",
            name="Invitation Space",
            description="Consent-based membership onboarding.",
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
            "invitee": invitee.id,
            "outsider": outsider.id,
        }


def test_owner_can_invite_existing_user_without_auto_membership(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    response = client.post(
        "/spaces/invitation-space/invitations",
        data={"username": "invite_target"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invitation sent to @invite_target" in response.data

    with app.app_context():
        invitation = SpaceInvitation.query.filter_by(
            space_id=ids["space"],
            invited_user_id=ids["invitee"],
        ).one()
        assert invitation.status == "pending"
        assert invitation.invited_by_id == ids["owner"]
        assert SpaceMembership.query.filter_by(
            space_id=ids["space"],
            user_id=ids["invitee"],
        ).first() is None
        assert Notification.query.filter_by(user_id=ids["invitee"]).count() == 1


def test_moderator_can_invite_but_ordinary_member_cannot(client, app):
    ids = _fixture(app)

    _login(client, ids["moderator"])
    assert client.post(
        "/spaces/invitation-space/invitations",
        data={"username": "invite_target"},
    ).status_code == 302

    with app.app_context():
        SpaceInvitation.query.delete()
        db.session.commit()

    _login(client, ids["member"])
    assert client.post(
        "/spaces/invitation-space/invitations",
        data={"username": "invite_target"},
    ).status_code == 403


def test_existing_member_and_duplicate_pending_invitation_are_rejected(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    assert client.post(
        "/spaces/invitation-space/invitations",
        data={"username": "invite_member"},
    ).status_code == 400

    assert client.post(
        "/spaces/invitation-space/invitations",
        data={"username": "invite_target"},
    ).status_code == 302
    duplicate = client.post(
        "/spaces/invitation-space/invitations",
        data={"username": "invite_target"},
        follow_redirects=True,
    )
    assert duplicate.status_code == 200
    assert b"already has a pending invitation" in duplicate.data

    with app.app_context():
        assert SpaceInvitation.query.filter_by(
            space_id=ids["space"],
            invited_user_id=ids["invitee"],
            status="pending",
        ).count() == 1


def test_invited_user_can_accept_and_membership_is_created_once(client, app):
    ids = _fixture(app)
    with app.app_context():
        invitation = SpaceInvitation(
            space_id=ids["space"],
            invited_user_id=ids["invitee"],
            invited_by_id=ids["owner"],
        )
        db.session.add(invitation)
        db.session.commit()
        invitation_id = invitation.id

    _login(client, ids["invitee"])
    response = client.post(
        f"/spaces/invitations/{invitation_id}/accept",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"You joined Invitation Space" in response.data

    with app.app_context():
        invitation = db.session.get(SpaceInvitation, invitation_id)
        assert invitation.status == "accepted"
        assert invitation.responded_at is not None
        membership = SpaceMembership.query.filter_by(
            space_id=ids["space"],
            user_id=ids["invitee"],
        ).one()
        assert membership.role == "member"

    assert client.post(f"/spaces/invitations/{invitation_id}/accept").status_code == 400
    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=ids["space"],
            user_id=ids["invitee"],
        ).count() == 1


def test_invited_user_can_decline_without_membership(client, app):
    ids = _fixture(app)
    with app.app_context():
        invitation = SpaceInvitation(
            space_id=ids["space"],
            invited_user_id=ids["invitee"],
            invited_by_id=ids["owner"],
        )
        db.session.add(invitation)
        db.session.commit()
        invitation_id = invitation.id

    _login(client, ids["invitee"])
    response = client.post(
        f"/spaces/invitations/{invitation_id}/decline",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"declined the invitation" in response.data

    with app.app_context():
        invitation = db.session.get(SpaceInvitation, invitation_id)
        assert invitation.status == "declined"
        assert SpaceMembership.query.filter_by(
            space_id=ids["space"],
            user_id=ids["invitee"],
        ).first() is None


def test_other_user_cannot_respond_to_someone_elses_invitation(client, app):
    ids = _fixture(app)
    with app.app_context():
        invitation = SpaceInvitation(
            space_id=ids["space"],
            invited_user_id=ids["invitee"],
            invited_by_id=ids["owner"],
        )
        db.session.add(invitation)
        db.session.commit()
        invitation_id = invitation.id

    _login(client, ids["outsider"])
    assert client.post(f"/spaces/invitations/{invitation_id}/accept").status_code == 404

    with app.app_context():
        assert db.session.get(SpaceInvitation, invitation_id).status == "pending"


def test_invitation_inbox_only_shows_current_users_pending_invitations(client, app):
    ids = _fixture(app)
    with app.app_context():
        db.session.add_all([
            SpaceInvitation(
                space_id=ids["space"],
                invited_user_id=ids["invitee"],
                invited_by_id=ids["owner"],
            ),
            SpaceInvitation(
                space_id=ids["space"],
                invited_user_id=ids["outsider"],
                invited_by_id=ids["owner"],
            ),
        ])
        db.session.commit()

    _login(client, ids["invitee"])
    page = client.get("/spaces/invitations")
    assert page.status_code == 200
    assert b"Invitation Space" in page.data
    assert page.data.count(b"Accept") == 1


def test_operator_dashboard_lists_pending_invitations_and_metric(client, app):
    ids = _fixture(app)
    with app.app_context():
        db.session.add(
            SpaceInvitation(
                space_id=ids["space"],
                invited_user_id=ids["invitee"],
                invited_by_id=ids["owner"],
            )
        )
        db.session.commit()

    _login(client, ids["moderator"])
    page = client.get("/spaces/invitation-space/operator")
    assert page.status_code == 200
    assert b"Pending invitations" in page.data
    assert b"invite_target" in page.data
    assert b'data-metric="pending-invitations">1<' in page.data


def test_owner_or_moderator_can_cancel_pending_invitation(client, app):
    ids = _fixture(app)
    with app.app_context():
        invitation = SpaceInvitation(
            space_id=ids["space"],
            invited_user_id=ids["invitee"],
            invited_by_id=ids["owner"],
        )
        db.session.add(invitation)
        db.session.commit()
        invitation_id = invitation.id

    _login(client, ids["moderator"])
    response = client.post(
        f"/spaces/invitation-space/invitations/{invitation_id}/cancel",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invitation to @invite_target canceled" in response.data

    with app.app_context():
        invitation = db.session.get(SpaceInvitation, invitation_id)
        assert invitation.status == "canceled"
        assert invitation.responded_at is not None

    _login(client, ids["invitee"])
    assert client.post(f"/spaces/invitations/{invitation_id}/accept").status_code == 400


def test_ordinary_member_cannot_cancel_invitation(client, app):
    ids = _fixture(app)
    with app.app_context():
        invitation = SpaceInvitation(
            space_id=ids["space"],
            invited_user_id=ids["invitee"],
            invited_by_id=ids["owner"],
        )
        db.session.add(invitation)
        db.session.commit()
        invitation_id = invitation.id

    _login(client, ids["member"])
    assert client.post(
        f"/spaces/invitation-space/invitations/{invitation_id}/cancel"
    ).status_code == 403

    with app.app_context():
        assert db.session.get(SpaceInvitation, invitation_id).status == "pending"
