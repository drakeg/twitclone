"""Sprint 13 Story 13.4 role, local moderation, audit, and appeal coverage."""

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.resource_models import Resource, ResourceRevision
from twitclone.spaces.models import (
    Space,
    SpaceMembership,
    SpaceModerationAction,
    SpaceModerationAppeal,
    SpacePost,
    SpaceResource,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="mod_owner", email="mod-owner@example.com", password="hash")
        moderator = User(username="mod_moderator", email="mod-moderator@example.com", password="hash")
        member = User(username="mod_member", email="mod-member@example.com", password="hash")
        outsider = User(username="mod_outsider", email="mod-outsider@example.com", password="hash")
        db.session.add_all([owner, moderator, member, outsider])
        db.session.flush()

        space = Space(slug="moderated-space", name="Moderated Space", description="Auditable local moderation", owner_id=owner.id)
        db.session.add(space)
        db.session.flush()
        owner_membership = SpaceMembership(space_id=space.id, user_id=owner.id, role="owner")
        moderator_membership = SpaceMembership(space_id=space.id, user_id=moderator.id, role="moderator")
        member_membership = SpaceMembership(space_id=space.id, user_id=member.id, role="member")
        db.session.add_all([owner_membership, moderator_membership, member_membership])

        tweet = Tweet(content="space content under review", user_id=member.id)
        db.session.add(tweet)
        db.session.flush()
        space_post = SpacePost(space_id=space.id, tweet_id=tweet.id)
        db.session.add(space_post)

        resource = Resource(owner_id=outsider.id, title="Global durable resource")
        db.session.add(resource)
        db.session.flush()
        revision = ResourceRevision(
            resource_id=resource.id,
            editor_id=outsider.id,
            revision_number=1,
            body="Durable resource body",
            change_note="Initial",
        )
        db.session.add(revision)
        db.session.flush()
        resource.current_revision_id = revision.id
        resource_link = SpaceResource(space_id=space.id, resource_id=resource.id, linked_by_id=member.id)
        db.session.add(resource_link)
        db.session.commit()
        return {
            "owner": owner.id,
            "moderator": moderator.id,
            "member": member.id,
            "outsider": outsider.id,
            "space": space.id,
            "member_membership": member_membership.id,
            "post": space_post.id,
            "tweet": tweet.id,
            "resource": resource.id,
            "resource_link": resource_link.id,
        }


def test_owner_can_promote_member_and_role_change_is_audited(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    response = client.post(
        f"/spaces/moderated-space/members/{ids['member']}/role",
        data={"role": "moderator"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"is now a moderator" in response.data
    with app.app_context():
        membership = db.session.get(SpaceMembership, ids["member_membership"])
        assert membership.role == "moderator"
        action = SpaceModerationAction.query.filter_by(
            space_id=ids["space"], action_type="promote_moderator", target_id=membership.id
        ).one()
        assert action.actor_id == ids["owner"]
        assert action.affected_user_id == ids["member"]


def test_nonmoderator_cannot_hide_space_post(client, app):
    ids = _fixture(app)
    _login(client, ids["member"])
    response = client.post(
        f"/spaces/moderated-space/posts/{ids['post']}/hide",
        data={"reason": "Trying to moderate without authority"},
    )
    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(SpacePost, ids["post"]).is_hidden is False


def test_moderator_hide_is_local_and_preserves_underlying_tweet(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])
    response = client.post(
        f"/spaces/moderated-space/posts/{ids['post']}/hide",
        data={"reason": "Off-topic for this space"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"underlying post was not globally deleted" in response.data
    assert b"space content under review" not in response.data
    with app.app_context():
        space_post = db.session.get(SpacePost, ids["post"])
        tweet = db.session.get(Tweet, ids["tweet"])
        assert space_post.is_hidden is True
        assert space_post.hidden_by_id == ids["moderator"]
        assert tweet.is_removed is False
        action = SpaceModerationAction.query.filter_by(
            space_id=ids["space"], action_type="hide_post", target_id=ids["post"]
        ).one()
        assert action.affected_user_id == ids["member"]


def test_moderator_hide_resource_is_local_and_preserves_durable_resource(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])
    response = client.post(
        f"/spaces/moderated-space/resources/{ids['resource_link']}/hide",
        data={"reason": "Not appropriate for this space knowledge list"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"durable resource was not deleted" in response.data
    with app.app_context():
        link = db.session.get(SpaceResource, ids["resource_link"])
        resource = db.session.get(Resource, ids["resource"])
        assert link.is_hidden is True
        assert resource.is_removed is False
        assert ResourceRevision.query.filter_by(resource_id=resource.id).count() == 1


def test_affected_member_can_appeal_and_owner_can_restore_local_post(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])
    client.post(
        f"/spaces/moderated-space/posts/{ids['post']}/hide",
        data={"reason": "Needs review"},
    )
    with app.app_context():
        action_id = SpaceModerationAction.query.filter_by(
            space_id=ids["space"], action_type="hide_post", target_id=ids["post"]
        ).one().id

    _login(client, ids["member"])
    response = client.post(
        f"/spaces/moderated-space/moderation/{action_id}/appeal",
        data={"rationale": "This belongs in the space because it answers the active topic."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Appeal submitted" in response.data
    with app.app_context():
        appeal_id = SpaceModerationAppeal.query.filter_by(action_id=action_id).one().id

    _login(client, ids["owner"])
    response = client.post(
        f"/spaces/moderated-space/appeals/{appeal_id}/resolve",
        data={"decision": "approved", "resolution_note": "Reviewed and restored to the space."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Appeal approved" in response.data
    with app.app_context():
        appeal = db.session.get(SpaceModerationAppeal, appeal_id)
        space_post = db.session.get(SpacePost, ids["post"])
        tweet = db.session.get(Tweet, ids["tweet"])
        assert appeal.status == "approved"
        assert appeal.resolved_by_id == ids["owner"]
        assert space_post.is_hidden is False
        assert tweet.is_removed is False
        assert SpaceModerationAction.query.filter_by(
            space_id=ids["space"], action_type="restore_post", target_id=ids["post"]
        ).count() == 1


def test_moderator_cannot_change_member_roles(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])
    response = client.post(
        f"/spaces/moderated-space/members/{ids['member']}/role",
        data={"role": "moderator"},
    )
    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(SpaceMembership, ids["member_membership"]).role == "member"
