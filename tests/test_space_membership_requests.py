"""Sprint 31 Story 31.1 private Space membership-request coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import (
    Space,
    SpaceMembership,
    SpaceMembershipRequest,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="request_owner", email="request-owner@example.com", password="hash")
        moderator = User(username="request_moderator", email="request-moderator@example.com", password="hash")
        requester = User(username="request_user", email="request-user@example.com", password="hash")
        outsider = User(username="request_outsider", email="request-outsider@example.com", password="hash")
        db.session.add_all([owner, moderator, requester, outsider])
        db.session.flush()

        private_space = Space(
            slug="private-request-space",
            name="Private Request Space",
            description="PRIVATE CONTENT MUST NOT LEAK",
            owner_id=owner.id,
            visibility="private",
        )
        public_space = Space(
            slug="public-request-space",
            name="Public Request Space",
            description="Public join path remains unchanged.",
            owner_id=owner.id,
            visibility="public",
        )
        db.session.add_all([private_space, public_space])
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=private_space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=private_space.id, user_id=moderator.id, role="moderator"),
            SpaceMembership(space_id=public_space.id, user_id=owner.id, role="owner"),
        ])
        db.session.commit()

        return {
            "private_space": private_space.id,
            "public_space": public_space.id,
            "private_slug": private_space.slug,
            "public_slug": public_space.slug,
            "owner": owner.id,
            "moderator": moderator.id,
            "requester": requester.id,
            "outsider": outsider.id,
        }


def _create_request(client, ids, note="Please consider my request."):
    _login(client, ids["requester"])
    return client.post(
        f"/spaces/{ids['private_slug']}/request-access",
        data={"note": note},
    )


def test_known_private_request_page_exposes_minimum_surface_not_private_content(client, app):
    ids = _fixture(app)
    _login(client, ids["requester"])

    detail = client.get(f"/spaces/{ids['private_slug']}")
    assert detail.status_code == 404

    request_page = client.get(f"/spaces/{ids['private_slug']}/request-access")
    assert request_page.status_code == 200
    assert b"Private Request Space" in request_page.data
    assert b"PRIVATE CONTENT MUST NOT LEAK" not in request_page.data
    assert b"request-owner@example.com" not in request_page.data
    assert b"request-moderator@example.com" not in request_page.data


def test_anonymous_request_page_redirects_to_login(client, app):
    ids = _fixture(app)

    response = client.get(f"/spaces/{ids['private_slug']}/request-access")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_public_space_uses_existing_detail_join_path_instead_of_request(client, app):
    ids = _fixture(app)
    _login(client, ids["requester"])

    response = client.get(f"/spaces/{ids['public_slug']}/request-access")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/spaces/{ids['public_slug']}")


def test_request_is_created_once_and_note_is_operator_only(client, app):
    ids = _fixture(app)

    response = _create_request(client, ids, note="Operator-only request note.")
    assert response.status_code == 302

    with app.app_context():
        row = SpaceMembershipRequest.query.filter_by(
            space_id=ids["private_space"],
            requester_id=ids["requester"],
            status="pending",
        ).one()
        assert row.note == "Operator-only request note."

    requester_page = client.get(f"/spaces/{ids['private_slug']}/request-access")
    assert requester_page.status_code == 200
    assert b"pending operator review" in requester_page.data
    assert b"Operator-only request note." in requester_page.data

    assert _create_request(client, ids, note="Duplicate").status_code == 302
    with app.app_context():
        assert SpaceMembershipRequest.query.filter_by(
            space_id=ids["private_space"],
            requester_id=ids["requester"],
            status="pending",
        ).count() == 1

    _login(client, ids["moderator"])
    operator_page = client.get(f"/spaces/{ids['private_slug']}/operator")
    assert operator_page.status_code == 200
    assert b"Operator-only request note." in operator_page.data
    assert b"request_user" in operator_page.data


def test_request_note_is_bounded(client, app):
    ids = _fixture(app)
    _login(client, ids["requester"])

    response = client.post(
        f"/spaces/{ids['private_slug']}/request-access",
        data={"note": "x" * 501},
    )
    assert response.status_code == 400

    with app.app_context():
        assert SpaceMembershipRequest.query.count() == 0


def test_owner_can_approve_request_exactly_once(client, app):
    ids = _fixture(app)
    _create_request(client, ids)

    with app.app_context():
        request_id = SpaceMembershipRequest.query.one().id

    _login(client, ids["owner"])
    response = client.post(
        f"/spaces/{ids['private_slug']}/membership-requests/{request_id}/approve"
    )
    assert response.status_code == 302

    with app.app_context():
        row = db.session.get(SpaceMembershipRequest, request_id)
        assert row.status == "approved"
        assert row.resolved_at is not None
        assert row.resolved_by_id == ids["owner"]
        memberships = SpaceMembership.query.filter_by(
            space_id=ids["private_space"],
            user_id=ids["requester"],
        ).all()
        assert len(memberships) == 1
        assert memberships[0].role == "member"

    second = client.post(
        f"/spaces/{ids['private_slug']}/membership-requests/{request_id}/approve"
    )
    assert second.status_code == 400

    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=ids["private_space"],
            user_id=ids["requester"],
        ).count() == 1


def test_moderator_can_deny_without_creating_membership(client, app):
    ids = _fixture(app)
    _create_request(client, ids)

    with app.app_context():
        request_id = SpaceMembershipRequest.query.one().id

    _login(client, ids["moderator"])
    response = client.post(
        f"/spaces/{ids['private_slug']}/membership-requests/{request_id}/deny"
    )
    assert response.status_code == 302

    with app.app_context():
        row = db.session.get(SpaceMembershipRequest, request_id)
        assert row.status == "denied"
        assert row.resolved_by_id == ids["moderator"]
        assert SpaceMembership.query.filter_by(
            space_id=ids["private_space"],
            user_id=ids["requester"],
        ).first() is None


def test_regular_nonoperator_cannot_resolve_request(client, app):
    ids = _fixture(app)
    _create_request(client, ids)

    with app.app_context():
        request_id = SpaceMembershipRequest.query.one().id

    _login(client, ids["outsider"])
    assert client.post(
        f"/spaces/{ids['private_slug']}/membership-requests/{request_id}/approve"
    ).status_code == 403


def test_pending_request_does_not_unlock_private_content(client, app):
    ids = _fixture(app)
    _create_request(client, ids)

    detail = client.get(f"/spaces/{ids['private_slug']}")
    assert detail.status_code == 404


def test_archived_private_space_blocks_request_and_resolution_mutations(client, app):
    ids = _fixture(app)

    with app.app_context():
        space = db.session.get(Space, ids["private_space"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["requester"])
    request_page = client.get(f"/spaces/{ids['private_slug']}/request-access")
    assert request_page.status_code == 200
    assert b"not accepting membership requests" in request_page.data
    assert client.post(
        f"/spaces/{ids['private_slug']}/request-access",
        data={"note": "Should be blocked"},
    ).status_code == 409

    with app.app_context():
        space = db.session.get(Space, ids["private_space"])
        space.archived_at = None
        space.archived_by_id = None
        db.session.commit()

    _create_request(client, ids)
    with app.app_context():
        request_id = SpaceMembershipRequest.query.one().id
        space = db.session.get(Space, ids["private_space"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["owner"])
    assert client.post(
        f"/spaces/{ids['private_slug']}/membership-requests/{request_id}/approve"
    ).status_code == 409


def test_resolution_audit_survives_operator_account_deletion(client, app):
    ids = _fixture(app)
    _create_request(client, ids)
    with app.app_context():
        request_id = SpaceMembershipRequest.query.one().id

    _login(client, ids["moderator"])
    assert client.post(
        f"/spaces/{ids['private_slug']}/membership-requests/{request_id}/deny"
    ).status_code == 302

    with app.app_context():
        moderator = db.session.get(User, ids["moderator"])
        db.session.delete(moderator)
        db.session.commit()

        row = db.session.get(SpaceMembershipRequest, request_id)
        assert row.status == "denied"
        assert row.resolved_at is not None
        assert row.resolved_by_id is None
        assert row.resolved_by is None
