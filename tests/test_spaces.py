"""Sprint 13 Story 13.1 persistent space foundation coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import Space, SpaceMembership


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user); db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_authenticated_user_can_create_space_and_becomes_owner(client, app):
    user_id = _user(app, "space_owner")
    _login(client, user_id)
    response = client.post(
        "/spaces/create",
        data={"name": "RV Travelers", "description": "A durable community for RV travel."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"RV Travelers" in response.data
    with app.app_context():
        space = Space.query.filter_by(slug="rv-travelers").one()
        membership = SpaceMembership.query.filter_by(space_id=space.id, user_id=user_id).one()
        assert space.owner_id == user_id
        assert membership.role == "owner"


def test_space_slug_must_be_unique(client, app):
    owner_id = _user(app, "space_unique_owner")
    _login(client, owner_id)
    first = client.post("/spaces/create", data={"name": "AWS Builders", "description": "First."})
    second = client.post("/spaces/create", data={"name": "AWS Builders", "description": "Second."})
    assert first.status_code == 302
    assert second.status_code == 400


def test_user_can_join_and_leave_public_space(client, app):
    owner_id = _user(app, "space_join_owner")
    member_id = _user(app, "space_join_member")
    with app.app_context():
        space = Space(slug="fitness", name="Fitness", description="Training talk.", owner_id=owner_id)
        db.session.add(space); db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner_id, role="owner")); db.session.commit()
    _login(client, member_id)
    assert client.post("/spaces/fitness/join").status_code == 302
    with app.app_context():
        assert SpaceMembership.query.filter_by(user_id=member_id).one().role == "member"
    assert client.post("/spaces/fitness/leave").status_code == 302
    with app.app_context():
        assert SpaceMembership.query.filter_by(user_id=member_id).first() is None


def test_owner_cannot_leave_without_transfer(client, app):
    owner_id = _user(app, "space_stay_owner")
    with app.app_context():
        space = Space(slug="owned", name="Owned", description="Owner boundary.", owner_id=owner_id)
        db.session.add(space); db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner_id, role="owner")); db.session.commit()
    _login(client, owner_id)
    response = client.post("/spaces/owned/leave")
    assert response.status_code == 400
    with app.app_context():
        assert SpaceMembership.query.filter_by(user_id=owner_id, role="owner").count() == 1


def test_spaces_are_publicly_discoverable(client, app):
    owner_id = _user(app, "space_public_owner")
    with app.app_context():
        db.session.add(Space(slug="linux", name="Linux", description="Linux community.", owner_id=owner_id)); db.session.commit()
    response = client.get("/spaces/")
    assert response.status_code == 200
    assert b"Linux" in response.data
    assert b"Membership does not affect your global reputation" in response.data


def test_owner_can_transfer_space_ownership_to_existing_member(client, app):
    owner_id = _user(app, "space_transfer_owner")
    member_id = _user(app, "space_transfer_member")
    with app.app_context():
        space = Space(
            slug="transferable",
            name="Transferable",
            description="Ownership can move safely.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
        ])
        db.session.commit()

    _login(client, owner_id)
    response = client.post(
        "/spaces/transferable/ownership",
        data={"user_id": member_id, "confirm": "transfer"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Ownership transferred" in response.data
    assert b"You remain a member and may now leave" in response.data

    with app.app_context():
        space = Space.query.filter_by(slug="transferable").one()
        owner_membership = SpaceMembership.query.filter_by(
            space_id=space.id, user_id=owner_id
        ).one()
        new_owner_membership = SpaceMembership.query.filter_by(
            space_id=space.id, user_id=member_id
        ).one()
        assert space.owner_id == member_id
        assert owner_membership.role == "member"
        assert new_owner_membership.role == "owner"


def test_transfer_requires_owner_and_explicit_confirmation(client, app):
    owner_id = _user(app, "space_transfer_guard_owner")
    member_id = _user(app, "space_transfer_guard_member")
    with app.app_context():
        space = Space(
            slug="guarded-transfer",
            name="Guarded Transfer",
            description="Transfer confirmation boundary.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
        ])
        db.session.commit()

    _login(client, member_id)
    assert client.post(
        "/spaces/guarded-transfer/ownership",
        data={"user_id": owner_id, "confirm": "transfer"},
    ).status_code == 403

    _login(client, owner_id)
    assert client.post(
        "/spaces/guarded-transfer/ownership",
        data={"user_id": member_id},
    ).status_code == 400

    with app.app_context():
        space = Space.query.filter_by(slug="guarded-transfer").one()
        assert space.owner_id == owner_id


def test_previous_owner_can_leave_after_transfer(client, app):
    owner_id = _user(app, "space_transfer_leave_owner")
    member_id = _user(app, "space_transfer_leave_member")
    with app.app_context():
        space = Space(
            slug="transfer-leave",
            name="Transfer Leave",
            description="Former owner can leave after transfer.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
        ])
        db.session.commit()

    _login(client, owner_id)
    assert client.post(
        "/spaces/transfer-leave/ownership",
        data={"user_id": member_id, "confirm": "transfer"},
    ).status_code == 302
    assert client.post("/spaces/transfer-leave/leave").status_code == 302

    with app.app_context():
        space = Space.query.filter_by(slug="transfer-leave").one()
        assert space.owner_id == member_id
        assert SpaceMembership.query.filter_by(
            space_id=space.id, user_id=owner_id
        ).first() is None
