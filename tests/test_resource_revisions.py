"""Sprint 11 Story 11.2 attributable revision coverage."""

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
        resource = Resource(owner_id=owner_id, title="AWS deployment guide")
        db.session.add(resource)
        db.session.flush()
        revision = ResourceRevision(
            resource_id=resource.id,
            editor_id=owner_id,
            revision_number=1,
            body="Original guidance",
            source_url="https://example.com/original",
            change_note="Initial version",
        )
        db.session.add(revision)
        db.session.flush()
        resource.current_revision_id = revision.id
        db.session.commit()
        return resource.id


def test_owner_publishes_new_attributed_revision(client, app):
    owner_id = _user(app, "resource_owner")
    resource_id = _resource(app, owner_id)
    _login(client, owner_id)

    response = client.post(
        f"/resources/{resource_id}/revise",
        data={
            "body": "Updated guidance",
            "source_url": "https://example.com/updated",
            "change_note": "Clarify the deployment steps",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Revision 2 published" in response.data
    assert b"Updated guidance" in response.data
    assert b"Clarify the deployment steps" in response.data

    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        assert [revision.revision_number for revision in resource.revisions] == [1, 2]
        assert resource.revisions[0].body == "Original guidance"
        assert resource.current_revision.body == "Updated guidance"
        assert resource.current_revision.editor_id == owner_id


def test_non_owner_cannot_publish_revision(client, app):
    owner_id = _user(app, "revision_owner")
    other_id = _user(app, "revision_other")
    resource_id = _resource(app, owner_id)
    _login(client, other_id)

    response = client.post(
        f"/resources/{resource_id}/revise",
        data={"body": "Unauthorized", "change_note": "Try overwrite"},
    )
    assert response.status_code == 403
    with app.app_context():
        assert ResourceRevision.query.filter_by(resource_id=resource_id).count() == 1


def test_admin_revision_is_attributed_to_admin(client, app):
    owner_id = _user(app, "admin_revision_owner")
    admin_id = _user(app, "resource_admin", admin=True)
    resource_id = _resource(app, owner_id)
    _login(client, admin_id)

    response = client.post(
        f"/resources/{resource_id}/revise",
        data={"body": "Admin correction", "change_note": "Correct broken guidance"},
    )
    assert response.status_code == 302
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        assert resource.current_revision.revision_number == 2
        assert resource.current_revision.editor_id == admin_id
        assert resource.revisions[0].editor_id == owner_id


def test_revision_requires_change_note_and_valid_source(client, app):
    owner_id = _user(app, "revision_validation_owner")
    resource_id = _resource(app, owner_id)
    _login(client, owner_id)

    missing_note = client.post(
        f"/resources/{resource_id}/revise",
        data={"body": "Updated", "change_note": ""},
    )
    assert missing_note.status_code == 400

    bad_source = client.post(
        f"/resources/{resource_id}/revise",
        data={"body": "Updated", "change_note": "Valid note", "source_url": "javascript:alert(1)"},
    )
    assert bad_source.status_code == 400
    with app.app_context():
        assert ResourceRevision.query.filter_by(resource_id=resource_id).count() == 1


def test_removed_resource_cannot_be_revised(client, app):
    owner_id = _user(app, "removed_revision_owner")
    resource_id = _resource(app, owner_id)
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        resource.is_removed = True
        db.session.commit()
    _login(client, owner_id)

    response = client.get(f"/resources/{resource_id}/revise")
    assert response.status_code == 404
