"""Sprint 13 Story 13.3 space resource/knowledge coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.resource_models import Resource, ResourceRevision
from twitclone.spaces.models import Space, SpaceMembership, SpaceResource


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="space_resource_owner", email="sr-owner@example.com", password="hash")
        member = User(username="space_resource_member", email="sr-member@example.com", password="hash")
        outsider = User(username="space_resource_outsider", email="sr-outsider@example.com", password="hash")
        db.session.add_all([owner, member, outsider]); db.session.flush()
        space = Space(slug="knowledge-space", name="Knowledge Space", description="Shared durable knowledge", owner_id=owner.id)
        db.session.add(space); db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
        ])
        resource = Resource(owner_id=outsider.id, title="Durable guide")
        db.session.add(resource); db.session.flush()
        revision = ResourceRevision(resource_id=resource.id, editor_id=outsider.id, revision_number=1, body="Original durable knowledge", change_note="Initial version")
        db.session.add(revision); db.session.flush(); resource.current_revision_id = revision.id
        db.session.commit()
        return owner.id, member.id, outsider.id, space.id, resource.id


def test_member_can_link_existing_resource_with_attribution(client, app):
    _, member_id, _, space_id, resource_id = _fixture(app)
    _login(client, member_id)
    response = client.post("/spaces/knowledge-space/resources", data={"resource_id": resource_id}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Durable guide" in response.data
    assert b"linked by @space_resource_member" in response.data
    with app.app_context():
        link = SpaceResource.query.filter_by(space_id=space_id, resource_id=resource_id).one()
        assert link.linked_by_id == member_id


def test_nonmember_cannot_link_resource(client, app):
    _, _, outsider_id, space_id, resource_id = _fixture(app)
    _login(client, outsider_id)
    response = client.post("/spaces/knowledge-space/resources", data={"resource_id": resource_id})
    assert response.status_code == 403
    with app.app_context():
        assert SpaceResource.query.filter_by(space_id=space_id, resource_id=resource_id).count() == 0


def test_removed_resource_is_hidden_and_cannot_be_newly_linked(client, app):
    _, member_id, _, space_id, resource_id = _fixture(app)
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        resource.is_removed = True
        db.session.commit()
    _login(client, member_id)
    response = client.post("/spaces/knowledge-space/resources", data={"resource_id": resource_id})
    assert response.status_code == 404
    public_response = client.get("/spaces/knowledge-space")
    assert b"Durable guide" not in public_response.data
    with app.app_context():
        assert SpaceResource.query.filter_by(space_id=space_id, resource_id=resource_id).count() == 0


def test_linking_does_not_copy_or_change_resource_ownership(client, app):
    _, member_id, outsider_id, _, resource_id = _fixture(app)
    _login(client, member_id)
    client.post("/spaces/knowledge-space/resources", data={"resource_id": resource_id})
    with app.app_context():
        resource = db.session.get(Resource, resource_id)
        assert resource.owner_id == outsider_id
        assert len(resource.revisions) == 1
        assert resource.current_revision.body == "Original durable knowledge"


def test_linker_can_remove_space_link_without_deleting_resource(client, app):
    _, member_id, _, space_id, resource_id = _fixture(app)
    _login(client, member_id)
    client.post("/spaces/knowledge-space/resources", data={"resource_id": resource_id})
    response = client.post(f"/spaces/knowledge-space/resources/{resource_id}/unlink", follow_redirects=True)
    assert response.status_code == 200
    assert b"No resources have been linked" in response.data
    with app.app_context():
        assert SpaceResource.query.filter_by(space_id=space_id, resource_id=resource_id).count() == 0
        assert db.session.get(Resource, resource_id) is not None
        assert ResourceRevision.query.filter_by(resource_id=resource_id).count() == 1


def test_other_member_cannot_remove_someone_elses_link(client, app):
    owner_id, member_id, _, space_id, resource_id = _fixture(app)
    _login(client, member_id)
    client.post("/spaces/knowledge-space/resources", data={"resource_id": resource_id})
    _login(client, owner_id)
    response = client.post(f"/spaces/knowledge-space/resources/{resource_id}/unlink")
    assert response.status_code == 403
    with app.app_context():
        assert SpaceResource.query.filter_by(space_id=space_id, resource_id=resource_id).count() == 1
