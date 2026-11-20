"""Sprint 28 Story 28.3 restore and lifecycle audit coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import (
    Space,
    SpaceLifecycleAction,
    SpaceMembership,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app, *, visibility="public", archived=True):
    with app.app_context():
        owner = User(username=f"lifecycle_owner_{visibility}_{archived}", email=f"lo-{visibility}-{archived}@example.com", password="hash")
        member = User(username=f"lifecycle_member_{visibility}_{archived}", email=f"lm-{visibility}-{archived}@example.com", password="hash")
        joiner = User(username=f"lifecycle_joiner_{visibility}_{archived}", email=f"lj-{visibility}-{archived}@example.com", password="hash")
        db.session.add_all([owner, member, joiner])
        db.session.flush()
        space = Space(
            slug=f"lifecycle-{visibility}-{int(archived)}",
            name="Lifecycle Space",
            description="Lifecycle audit coverage.",
            owner_id=owner.id,
            visibility=visibility,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
        ])
        if archived:
            space.archived_at = space.created_at
            space.archived_by_id = owner.id
        db.session.commit()
        return {
            "space": space.id,
            "slug": space.slug,
            "owner": owner.id,
            "member": member.id,
            "joiner": joiner.id,
        }


def test_owner_can_restore_archived_public_space_and_resume_join(client, app):
    ids = _fixture(app, visibility="public", archived=True)
    _login(client, ids["owner"])

    response = client.post(
        f"/spaces/{ids['slug']}/restore",
        data={"confirm": "restore"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"was restored" in response.data

    with app.app_context():
        space = db.session.get(Space, ids["space"])
        assert space.archived_at is None
        assert space.archived_by_id is None
        assert space.slug == ids["slug"]
        assert space.visibility == "public"
        action = SpaceLifecycleAction.query.filter_by(
            space_id=space.id,
            action_type="restored",
        ).one()
        assert action.actor_id == ids["owner"]

    _login(client, ids["joiner"])
    assert client.post(f"/spaces/{ids['slug']}/join").status_code == 302


def test_restored_private_space_remains_private(client, app):
    ids = _fixture(app, visibility="private", archived=True)
    _login(client, ids["owner"])
    assert client.post(
        f"/spaces/{ids['slug']}/restore",
        data={"confirm": "restore"},
    ).status_code == 302

    _login(client, ids["joiner"])
    assert client.get(f"/spaces/{ids['slug']}").status_code == 404
    assert client.post(f"/spaces/{ids['slug']}/join").status_code == 403


def test_nonowner_cannot_restore_space(client, app):
    ids = _fixture(app, archived=True)
    _login(client, ids["member"])
    assert client.post(
        f"/spaces/{ids['slug']}/restore",
        data={"confirm": "restore"},
    ).status_code == 403
    with app.app_context():
        assert db.session.get(Space, ids["space"]).archived_at is not None


def test_restore_requires_confirmation(client, app):
    ids = _fixture(app, archived=True)
    _login(client, ids["owner"])
    assert client.post(f"/spaces/{ids['slug']}/restore").status_code == 400


def test_settings_update_creates_lifecycle_audit(client, app):
    ids = _fixture(app, visibility="public", archived=False)
    _login(client, ids["owner"])
    response = client.post(
        f"/spaces/{ids['slug']}/settings",
        data={
            "name": "Lifecycle Renamed",
            "description": "Updated lifecycle description.",
            "visibility": "private",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        action = SpaceLifecycleAction.query.filter_by(
            space_id=ids["space"],
            action_type="settings_updated",
        ).one()
        assert action.previous_name == "Lifecycle Space"
        assert action.new_name == "Lifecycle Renamed"
        assert action.previous_visibility == "public"
        assert action.new_visibility == "private"
        assert action.details == "description_updated"


def test_archive_creates_lifecycle_audit(client, app):
    ids = _fixture(app, archived=False)
    _login(client, ids["owner"])
    assert client.post(
        f"/spaces/{ids['slug']}/archive",
        data={"confirm": "archive"},
    ).status_code == 302

    with app.app_context():
        action = SpaceLifecycleAction.query.filter_by(
            space_id=ids["space"],
            action_type="archived",
        ).one()
        assert action.actor_id == ids["owner"]
        assert action.previous_visibility == "public"
        assert action.new_visibility == "public"


def test_lifecycle_history_is_owner_only_on_operator_dashboard(client, app):
    ids = _fixture(app, archived=False)
    _login(client, ids["owner"])
    client.post(
        f"/spaces/{ids['slug']}/settings",
        data={
            "name": "Lifecycle History",
            "description": "History visible to owner.",
            "visibility": "public",
        },
    )

    owner_page = client.get(f"/spaces/{ids['slug']}/operator")
    assert owner_page.status_code == 200
    assert b"Space lifecycle history" in owner_page.data
    assert b"Settings Updated" in owner_page.data

    _login(client, ids["member"])
    member_page = client.get(f"/spaces/{ids['slug']}/operator")
    assert member_page.status_code == 403
