"""Sprint 11 Story 11.3 revision inspection and comparison coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.resource_models import Resource, ResourceRevision


def _resource_with_revisions(app):
    with app.app_context():
        user = User(username="revision_reader", email="revision-reader@example.com", password="hash")
        db.session.add(user)
        db.session.flush()
        resource = Resource(owner_id=user.id, title="Camping checklist")
        db.session.add(resource)
        db.session.flush()
        first = ResourceRevision(
            resource_id=resource.id,
            editor_id=user.id,
            revision_number=1,
            body="Water\nFood\nFlashlight",
            source_url="https://example.com/one",
            change_note="Initial version",
        )
        second = ResourceRevision(
            resource_id=resource.id,
            editor_id=user.id,
            revision_number=2,
            body="Water\nFood\nFirst aid kit\nFlashlight",
            source_url="https://example.com/two",
            change_note="Add first aid supplies",
        )
        db.session.add_all([first, second])
        db.session.flush()
        resource.current_revision_id = second.id
        db.session.commit()
        return resource.id


def test_revision_history_links_to_inspectable_versions(client, app):
    resource_id = _resource_with_revisions(app)
    response = client.get(f"/resources/{resource_id}")
    assert response.status_code == 200
    assert f"/resources/{resource_id}/revisions/1".encode() in response.data
    assert f"/resources/{resource_id}/revisions/2".encode() in response.data
    assert b"current" in response.data


def test_historical_revision_shows_exact_content_and_comparison(client, app):
    resource_id = _resource_with_revisions(app)
    response = client.get(f"/resources/{resource_id}/revisions/2")
    assert response.status_code == 200
    assert b"Water" in response.data
    assert b"First aid kit" in response.data
    assert b"Changes from revision 1" in response.data
    assert b"Added:" in response.data
    assert b"Add first aid supplies" in response.data
    assert b"Current" in response.data


def test_initial_revision_has_no_fake_previous_comparison(client, app):
    resource_id = _resource_with_revisions(app)
    response = client.get(f"/resources/{resource_id}/revisions/1")
    assert response.status_code == 200
    assert b"Initial revision" in response.data
    assert b"no earlier revision to compare" in response.data
    assert b"Historical" in response.data


def test_unknown_revision_returns_404(client, app):
    resource_id = _resource_with_revisions(app)
    response = client.get(f"/resources/{resource_id}/revisions/99")
    assert response.status_code == 404


def test_removed_resource_revision_is_not_public(client, app):
    resource_id = _resource_with_revisions(app)
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        resource.is_removed = True
        db.session.commit()
    response = client.get(f"/resources/{resource_id}/revisions/1")
    assert response.status_code == 404
