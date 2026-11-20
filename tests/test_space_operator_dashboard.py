"""Commercialization pilot: community operator dashboard coverage."""

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.spaces.models import (
    Space,
    SpaceMembership,
    SpaceModerationAction,
    SpaceModerationAppeal,
    SpacePost,
)


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _space_with_roles(app):
    owner_id = _user(app, "operator_owner")
    moderator_id = _user(app, "operator_moderator")
    member_id = _user(app, "operator_member")
    with app.app_context():
        space = Space(
            slug="operator-space",
            name="Operator Space",
            description="Operator dashboard test space.",
            owner_id=owner_id,
        )
        db.session.add(space)
        db.session.flush()
        owner_membership = SpaceMembership(space_id=space.id, user_id=owner_id, role="owner")
        moderator_membership = SpaceMembership(
            space_id=space.id,
            user_id=moderator_id,
            role="moderator",
        )
        member_membership = SpaceMembership(space_id=space.id, user_id=member_id, role="member")
        db.session.add_all([owner_membership, moderator_membership, member_membership])
        db.session.flush()

        visible = Tweet(content="Visible operator activity", user_id=member_id)
        hidden = Tweet(content="Hidden operator activity", user_id=member_id)
        db.session.add_all([visible, hidden])
        db.session.flush()
        visible_row = SpacePost(space_id=space.id, tweet_id=visible.id)
        hidden_row = SpacePost(space_id=space.id, tweet_id=hidden.id, is_hidden=True)
        db.session.add_all([visible_row, hidden_row])
        db.session.flush()

        action = SpaceModerationAction(
            space_id=space.id,
            actor_id=moderator_id,
            action_type="hide_post",
            target_type="post",
            target_id=hidden_row.id,
            affected_user_id=member_id,
            reason="Test moderation action.",
        )
        db.session.add(action)
        db.session.flush()
        db.session.add(
            SpaceModerationAppeal(
                space_id=space.id,
                action_id=action.id,
                requester_id=member_id,
                rationale="Please review this test action.",
            )
        )
        db.session.commit()
        return {
            "slug": space.slug,
            "owner_id": owner_id,
            "moderator_id": moderator_id,
            "member_id": member_id,
        }


def test_owner_sees_operator_dashboard_with_real_metrics(client, app):
    context = _space_with_roles(app)
    _login(client, context["owner_id"])

    response = client.get(f"/spaces/{context['slug']}/operator")

    assert response.status_code == 200
    assert b"Community operating summary" in response.data
    assert b'data-metric="member-count">3<' in response.data
    assert b'data-metric="moderator-count">2<' in response.data
    assert b'data-metric="new-members-30d">3<' in response.data
    assert b'data-metric="posts-30d">1<' in response.data
    assert b'data-metric="resources-30d">0<' in response.data
    assert b'data-metric="pending-appeals">1<' in response.data
    assert b'data-metric="moderation-actions-30d">1<' in response.data
    assert b"Manage member roles" in response.data


def test_moderator_can_view_dashboard_without_owner_role_controls(client, app):
    context = _space_with_roles(app)
    _login(client, context["moderator_id"])

    response = client.get(f"/spaces/{context['slug']}/operator")

    assert response.status_code == 200
    assert b"Community operating summary" in response.data
    assert b"Review moderation and appeals" in response.data
    assert b"Manage member roles" not in response.data


def test_regular_member_cannot_view_operator_dashboard(client, app):
    context = _space_with_roles(app)
    _login(client, context["member_id"])

    response = client.get(f"/spaces/{context['slug']}/operator")

    assert response.status_code == 403


def test_anonymous_user_is_redirected_to_login_for_operator_dashboard(client, app):
    context = _space_with_roles(app)

    response = client.get(f"/spaces/{context['slug']}/operator")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_space_detail_links_operator_dashboard_only_for_moderators(client, app):
    context = _space_with_roles(app)

    _login(client, context["moderator_id"])
    moderator_response = client.get(f"/spaces/{context['slug']}")
    assert moderator_response.status_code == 200
    operator_href = f"/spaces/{context['slug']}/operator".encode()
    assert operator_href in moderator_response.data

    _login(client, context["member_id"])
    member_response = client.get(f"/spaces/{context['slug']}")
    assert member_response.status_code == 200
    assert operator_href not in member_response.data
