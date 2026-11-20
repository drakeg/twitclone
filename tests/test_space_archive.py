"""Sprint 28 Story 28.2 reversible Space archive coverage."""

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.resource_models import Resource
from twitclone.spaces.models import (
    Space,
    SpaceInvitation,
    SpaceMembership,
    SpacePost,
    SpaceResource,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="archive_owner", email="archive-owner@example.com", password="hash")
        member = User(username="archive_member", email="archive-member@example.com", password="hash")
        invitee = User(username="archive_invitee", email="archive-invitee@example.com", password="hash")
        db.session.add_all([owner, member, invitee])
        db.session.flush()
        space = Space(
            slug="archive-space",
            name="Archive Space",
            description="Reversible lifecycle state.",
            owner_id=owner.id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
        ])
        tweet = Tweet(content="Preserved history", user_id=member.id)
        resource = Resource(owner_id=member.id, title="Preserved resource")
        db.session.add_all([tweet, resource])
        db.session.flush()
        db.session.add_all([
            SpacePost(space_id=space.id, tweet_id=tweet.id),
            SpaceResource(space_id=space.id, resource_id=resource.id, linked_by_id=member.id),
        ])
        invitation = SpaceInvitation(
            space_id=space.id,
            invited_user_id=invitee.id,
            invited_by_id=owner.id,
        )
        db.session.add(invitation)
        db.session.commit()
        return {
            "space": space.id,
            "owner": owner.id,
            "member": member.id,
            "invitee": invitee.id,
            "invitation": invitation.id,
            "resource": resource.id,
        }


def test_owner_can_archive_space_without_deleting_history(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    response = client.post(
        "/spaces/archive-space/archive",
        data={"confirm": "archive"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"was archived" in response.data
    assert b"Archived space" in response.data
    assert b"Preserved history" in response.data

    with app.app_context():
        space = db.session.get(Space, ids["space"])
        assert space.archived_at is not None
        assert space.archived_by_id == ids["owner"]
        assert SpaceMembership.query.filter_by(space_id=space.id).count() == 2
        assert SpacePost.query.filter_by(space_id=space.id).count() == 1
        assert SpaceResource.query.filter_by(space_id=space.id).count() == 1
        assert SpaceInvitation.query.filter_by(space_id=space.id).count() == 1


def test_nonowner_cannot_archive_space(client, app):
    ids = _fixture(app)
    _login(client, ids["member"])
    assert client.post(
        "/spaces/archive-space/archive",
        data={"confirm": "archive"},
    ).status_code == 403
    with app.app_context():
        assert db.session.get(Space, ids["space"]).archived_at is None


def test_archive_requires_explicit_confirmation(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    assert client.post("/spaces/archive-space/archive").status_code == 400
    with app.app_context():
        assert db.session.get(Space, ids["space"]).archived_at is None


def test_archived_space_blocks_new_participation(client, app):
    ids = _fixture(app)
    with app.app_context():
        space = db.session.get(Space, ids["space"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["member"])
    assert client.post(
        "/spaces/archive-space/posts",
        data={"content": "Should not publish"},
    ).status_code == 409
    assert client.post(
        "/spaces/archive-space/resources",
        data={"resource_id": ids["resource"]},
    ).status_code == 409

    _login(client, ids["owner"])
    assert client.post(
        "/spaces/archive-space/invitations",
        data={"username": "archive_invitee"},
    ).status_code == 409
    assert client.post(
        "/spaces/archive-space/settings",
        data={
            "name": "Changed",
            "description": "Should stay frozen",
            "visibility": "private",
        },
    ).status_code == 409

    _login(client, ids["invitee"])
    assert client.post(
        f"/spaces/invitations/{ids['invitation']}/accept"
    ).status_code == 409
    assert client.post("/spaces/archive-space/join").status_code == 409


def test_archived_space_still_allows_existing_member_to_leave(client, app):
    ids = _fixture(app)
    with app.app_context():
        space = db.session.get(Space, ids["space"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["member"])
    assert client.post("/spaces/archive-space/leave").status_code == 302

    with app.app_context():
        assert SpaceMembership.query.filter_by(
            space_id=ids["space"],
            user_id=ids["member"],
        ).first() is None
