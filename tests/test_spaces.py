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


def test_owner_can_remove_nonowner_member(client, app):
    owner_id = _user(app, "space_remove_owner")
    member_id = _user(app, "space_remove_member")
    with app.app_context():
        space = Space(
            slug="remove-member",
            name="Remove Member",
            description="Owner membership administration.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
        ])
        db.session.commit()
        space_id = space.id

    _login(client, owner_id)
    response = client.post(
        f"/spaces/remove-member/members/{member_id}/remove",
        data={"confirm": "remove"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"was removed from Remove Member" in response.data
    assert b"they may join again" in response.data

    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=space_id, user_id=member_id
        ).first() is None


def test_nonowner_cannot_remove_member(client, app):
    owner_id = _user(app, "space_remove_guard_owner")
    member_id = _user(app, "space_remove_guard_member")
    other_id = _user(app, "space_remove_guard_other")
    with app.app_context():
        space = Space(
            slug="remove-guard",
            name="Remove Guard",
            description="Removal authorization boundary.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
            SpaceMembership(space_id=space.id, user_id=other_id, role="member"),
        ])
        db.session.commit()
        space_id = space.id

    _login(client, member_id)
    assert client.post(
        f"/spaces/remove-guard/members/{other_id}/remove",
        data={"confirm": "remove"},
    ).status_code == 403

    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=space_id, user_id=other_id
        ).count() == 1


def test_owner_removal_requires_confirmation_and_cannot_target_owner(client, app):
    owner_id = _user(app, "space_remove_confirm_owner")
    member_id = _user(app, "space_remove_confirm_member")
    with app.app_context():
        space = Space(
            slug="remove-confirm",
            name="Remove Confirm",
            description="Removal confirmation boundary.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
        ])
        db.session.commit()
        space_id = space.id

    _login(client, owner_id)
    assert client.post(
        f"/spaces/remove-confirm/members/{member_id}/remove"
    ).status_code == 400
    assert client.post(
        f"/spaces/remove-confirm/members/{owner_id}/remove",
        data={"confirm": "remove"},
    ).status_code == 400

    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=space_id, user_id=member_id
        ).count() == 1


def test_removed_member_can_rejoin_public_space(client, app):
    owner_id = _user(app, "space_remove_rejoin_owner")
    member_id = _user(app, "space_remove_rejoin_member")
    with app.app_context():
        space = Space(
            slug="remove-rejoin",
            name="Remove Rejoin",
            description="Public spaces remain joinable.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
        ])
        db.session.commit()
        space_id = space.id

    _login(client, owner_id)
    assert client.post(
        f"/spaces/remove-rejoin/members/{member_id}/remove",
        data={"confirm": "remove"},
    ).status_code == 302

    _login(client, member_id)
    assert client.post("/spaces/remove-rejoin/join").status_code == 302

    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=space_id, user_id=member_id
        ).one().role == "member"


def test_private_space_is_hidden_from_anonymous_and_nonmembers(client, app):
    owner_id = _user(app, "private_owner")
    member_id = _user(app, "private_nonmember")
    with app.app_context():
        space = Space(
            slug="private-club",
            name="Private Club",
            description="Invitation-only discussion.",
            owner_id=owner_id,
            visibility="private",
        )
        db.session.add(space)
        db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"))
        db.session.commit()

    index = client.get("/spaces/")
    assert b"Private Club" not in index.data
    assert client.get("/spaces/private-club").status_code == 404

    _login(client, member_id)
    assert client.get("/spaces/private-club").status_code == 404
    assert client.post("/spaces/private-club/join").status_code == 403


def test_private_space_member_can_discover_and_view_space(client, app):
    owner_id = _user(app, "private_member_owner")
    member_id = _user(app, "private_member")
    with app.app_context():
        space = Space(
            slug="member-private",
            name="Member Private",
            description="Visible only to members.",
            owner_id=owner_id,
            visibility="private",
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member_id, role="member"),
        ])
        db.session.commit()

    _login(client, member_id)
    index = client.get("/spaces/")
    assert b"Member Private" in index.data
    detail = client.get("/spaces/member-private")
    assert detail.status_code == 200
    assert b"Private" in detail.data


def test_user_can_create_private_space(client, app):
    owner_id = _user(app, "private_create_owner")
    _login(client, owner_id)
    response = client.post(
        "/spaces/create",
        data={
            "name": "Invite Only",
            "description": "Private-by-choice space.",
            "visibility": "private",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        space = Space.query.filter_by(slug="invite-only").one()
        assert space.visibility == "private"
        assert SpaceMembership.query.filter_by(
            space_id=space.id, user_id=owner_id, role="owner"
        ).count() == 1


def test_public_space_join_and_discovery_remain_unchanged(client, app):
    owner_id = _user(app, "public_compat_owner")
    joiner_id = _user(app, "public_compat_joiner")
    with app.app_context():
        space = Space(
            slug="public-compat",
            name="Public Compat",
            description="Existing public behavior.",
            owner_id=owner_id,
            visibility="public",
        )
        db.session.add(space)
        db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"))
        db.session.commit()

    assert b"Public Compat" in client.get("/spaces/").data
    assert client.get("/spaces/public-compat").status_code == 200
    _login(client, joiner_id)
    assert client.post("/spaces/public-compat/join").status_code == 302


def test_owner_can_update_space_settings_without_changing_slug(client, app):
    owner_id = _user(app, "space_settings_owner")
    with app.app_context():
        space = Space(
            slug="stable-url",
            name="Original Name",
            description="Original description.",
            owner_id=owner_id,
            visibility="public",
        )
        db.session.add(space)
        db.session.flush()
        space_id = space.id
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"))
        db.session.commit()

    _login(client, owner_id)
    response = client.post(
        "/spaces/stable-url/settings",
        data={
            "name": "Updated Name",
            "description": "Updated description for the community.",
            "visibility": "private",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Space settings updated" in response.data
    assert b"Updated Name" in response.data

    with app.app_context():
        space = db.session.get(Space, space_id)
        assert space.slug == "stable-url"
        assert space.name == "Updated Name"
        assert space.description == "Updated description for the community."
        assert space.visibility == "private"


def test_nonowner_cannot_edit_space_settings(client, app):
    owner_id = _user(app, "space_settings_guard_owner")
    member_id = _user(app, "space_settings_guard_member")
    with app.app_context():
        space = Space(
            slug="settings-guard",
            name="Settings Guard",
            description="Owner-only settings.",
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
    assert client.get("/spaces/settings-guard/settings").status_code == 403
    assert client.post(
        "/spaces/settings-guard/settings",
        data={"name": "Hijacked", "description": "No.", "visibility": "private"},
    ).status_code == 403


def test_space_settings_validate_fields(client, app):
    owner_id = _user(app, "space_settings_validation_owner")
    with app.app_context():
        space = Space(
            slug="settings-validation",
            name="Settings Validation",
            description="Validation boundaries.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"))
        db.session.commit()

    _login(client, owner_id)
    response = client.post(
        "/spaces/settings-validation/settings",
        data={"name": "", "description": "", "visibility": "secret"},
    )
    assert response.status_code == 400

    with app.app_context():
        space = Space.query.filter_by(slug="settings-validation").one()
        assert space.name == "Settings Validation"
        assert space.description == "Validation boundaries."
        assert space.visibility == "public"


def test_switching_private_to_public_reopens_discovery_and_join(client, app):
    owner_id = _user(app, "space_visibility_owner")
    joiner_id = _user(app, "space_visibility_joiner")
    with app.app_context():
        space = Space(
            slug="visibility-switch",
            name="Visibility Switch",
            description="Visibility changes safely.",
            owner_id=owner_id,
            visibility="private",
        )
        db.session.add(space)
        db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner_id, role="owner"))
        db.session.commit()

    assert b"Visibility Switch" not in client.get("/spaces/").data
    _login(client, owner_id)
    assert client.post(
        "/spaces/visibility-switch/settings",
        data={
            "name": "Visibility Switch",
            "description": "Visibility changes safely.",
            "visibility": "public",
        },
    ).status_code == 302

    _login(client, joiner_id)
    assert b"Visibility Switch" in client.get("/spaces/").data
    assert client.post("/spaces/visibility-switch/join").status_code == 302
