"""Sprint 11 Story 11.5 resource lifecycle integrity coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.resource_models import Resource, ResourceRevision


def _user(app, username, *, admin=False):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash", is_admin=admin)
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _resource(app, owner_id):
    with app.app_context():
        resource = Resource(owner_id=owner_id, title="Lifecycle guide")
        db.session.add(resource)
        db.session.flush()
        first = ResourceRevision(resource_id=resource.id, editor_id=owner_id, revision_number=1, body="Original", change_note="Initial version")
        second = ResourceRevision(resource_id=resource.id, editor_id=owner_id, revision_number=2, body="Corrected", change_note="Correct guidance")
        db.session.add_all([first, second])
        db.session.flush()
        resource.current_revision_id = second.id
        db.session.commit()
        return resource.id


def test_owner_removal_preserves_revision_provenance(client, app):
    owner_id = _user(app, "lifecycle_owner")
    resource_id = _resource(app, owner_id)
    _login(client, owner_id)

    response = client.post(f"/resources/{resource_id}/remove", data={"reason": "No longer safe guidance"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"revision provenance remains preserved" in response.data
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        assert resource.is_removed is True
        assert resource.removed_by_id == owner_id
        assert resource.removed_at is not None
        assert resource.removal_reason == "No longer safe guidance"
        assert [(r.revision_number, r.body) for r in resource.revisions] == [(1, "Original"), (2, "Corrected")]

    assert client.get(f"/resources/{resource_id}").status_code == 404
    assert client.get(f"/resources/{resource_id}/revisions/1").status_code == 404


def test_non_owner_cannot_remove_resource(client, app):
    owner_id = _user(app, "lifecycle_owner_two")
    other_id = _user(app, "lifecycle_other")
    resource_id = _resource(app, owner_id)
    _login(client, other_id)

    response = client.post(f"/resources/{resource_id}/remove", data={"reason": "Try remove"})
    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(Resource, resource_id).is_removed is False


def test_admin_removal_is_attributed_to_admin(client, app):
    owner_id = _user(app, "admin_lifecycle_owner")
    admin_id = _user(app, "lifecycle_admin", admin=True)
    resource_id = _resource(app, owner_id)
    _login(client, admin_id)

    response = client.post(f"/resources/{resource_id}/remove", data={"reason": "Community Standards violation"})
    assert response.status_code == 302
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        assert resource.is_removed is True
        assert resource.removed_by_id == admin_id
        assert resource.removal_reason == "Community Standards violation"


def test_removal_requires_retained_reason(client, app):
    owner_id = _user(app, "reason_owner")
    resource_id = _resource(app, owner_id)
    _login(client, owner_id)

    response = client.post(f"/resources/{resource_id}/remove", data={"reason": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"removal reason" in response.data
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        assert resource.is_removed is False
        assert resource.removed_at is None


def test_removed_resource_cannot_receive_future_revision(client, app):
    owner_id = _user(app, "removed_future_owner")
    resource_id = _resource(app, owner_id)
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        resource.is_removed = True
        resource.removal_reason = "Removed"
        db.session.commit()
    _login(client, owner_id)

    assert client.post(f"/resources/{resource_id}/revise", data={"body": "Third", "change_note": "Try revise"}).status_code == 404
