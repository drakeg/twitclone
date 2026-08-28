"""Sprint 11 Story 11.4 resource discovery coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import User
from twitclone.resource_models import Resource, ResourceRevision, ResourceTopic
from twitclone.topic_models import Topic


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _setup(app):
    with app.app_context():
        viewer = User(username="resource_viewer", email="viewer@example.com", password="hash")
        owner = User(username="resource_writer", email="writer@example.com", password="hash")
        topic = Topic(name="AWS", slug="aws")
        db.session.add_all([viewer, owner, topic])
        db.session.flush()
        db.session.commit()
        return viewer.id, owner.id, topic.id


def _resource(app, owner_id, topic_id, title, *, updated_at, removed=False):
    with app.app_context():
        resource = Resource(owner_id=owner_id, title=title, is_removed=removed, updated_at=updated_at)
        db.session.add(resource)
        db.session.flush()
        revision = ResourceRevision(
            resource_id=resource.id,
            editor_id=owner_id,
            revision_number=1,
            body=f"Durable guidance for {title}",
            change_note="Initial version",
        )
        db.session.add(revision)
        db.session.flush()
        resource.current_revision_id = revision.id
        db.session.add(ResourceTopic(resource_id=resource.id, topic_id=topic_id))
        db.session.commit()
        return resource.id


def test_topic_page_surfaces_explicit_resources_newest_first(client, app):
    viewer_id, owner_id, topic_id = _setup(app)
    now = datetime.now(UTC).replace(tzinfo=None)
    older_id = _resource(app, owner_id, topic_id, "Older guide", updated_at=now - timedelta(days=1))
    newer_id = _resource(app, owner_id, topic_id, "Newer guide", updated_at=now)
    _login(client, viewer_id)

    response = client.get("/topic/aws")
    assert response.status_code == 200
    assert b"Resources about AWS" in response.data
    assert response.data.index(b"Newer guide") < response.data.index(b"Older guide")
    assert f"/resources/{newer_id}".encode() in response.data
    assert f"/resources/{older_id}".encode() in response.data
    assert b"paid plans" in response.data
    assert b"do not buy placement" in response.data


def test_removed_resource_is_excluded_from_topic_discovery(client, app):
    viewer_id, owner_id, topic_id = _setup(app)
    now = datetime.now(UTC).replace(tzinfo=None)
    _resource(app, owner_id, topic_id, "Visible guide", updated_at=now)
    _resource(app, owner_id, topic_id, "Removed guide", updated_at=now + timedelta(minutes=1), removed=True)
    _login(client, viewer_id)

    response = client.get("/topic/aws")
    assert b"Visible guide" in response.data
    assert b"Removed guide" not in response.data


def test_topic_without_resources_has_clear_empty_state(client, app):
    viewer_id, _, _ = _setup(app)
    _login(client, viewer_id)

    response = client.get("/topic/aws")
    assert response.status_code == 200
    assert b"No resources yet" in response.data
    assert b"no visible durable resources yet" in response.data
