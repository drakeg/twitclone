"""Sprint 11 Story 11.1 collaborative resource foundation coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.resource_models import Resource, ResourceRevision, ResourceTopic


def _user(app, username="resource_author"):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_resource_creation_starts_attributable_revision_history(client, app):
    user_id = _user(app)
    _login(client, user_id)
    response = client.post(
        "/resources/new",
        data={
            "title": "AWS container checklist",
            "body": "A durable checklist for container deployments.",
            "source_url": "https://docs.aws.amazon.com/",
            "topics": "AWS, Containers, AWS",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Revision 1" in response.data
    assert b"AWS container checklist" in response.data

    with app.app_context():
        resource = Resource.query.one()
        revision = ResourceRevision.query.one()
        assert resource.owner_id == user_id
        assert resource.current_revision_id == revision.id
        assert revision.editor_id == user_id
        assert revision.revision_number == 1
        assert revision.change_note == "Initial version"
        assert {row.topic.slug for row in ResourceTopic.query.all()} == {"aws", "containers"}


def test_resource_creation_requires_login(client):
    response = client.get("/resources/new")
    assert response.status_code in {302, 401}


def test_resource_rejects_non_http_source(client, app):
    user_id = _user(app, "bad_source")
    _login(client, user_id)
    response = client.post(
        "/resources/new",
        data={"title": "Bad source", "body": "Body", "source_url": "javascript:alert(1)"},
    )
    assert response.status_code == 400
    with app.app_context():
        assert Resource.query.count() == 0


def test_removed_resource_is_not_listed_or_viewable(client, app):
    user_id = _user(app, "removed_resource")
    with app.app_context():
        resource = Resource(owner_id=user_id, title="Removed guide", is_removed=True)
        db.session.add(resource)
        db.session.flush()
        db.session.add(ResourceRevision(resource_id=resource.id, editor_id=user_id, revision_number=1, body="Old content"))
        db.session.commit()
        resource_id = resource.id

    assert b"Removed guide" not in client.get("/resources/").data
    assert client.get(f"/resources/{resource_id}").status_code == 404


def test_resource_index_has_graceful_empty_state(client):
    response = client.get("/resources/")
    assert response.status_code == 200
    assert b"No resources yet" in response.data
