"""Sprint 30 Story 30.1 Space conversation pinning coverage."""

from datetime import datetime

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.spaces.models import (
    Space,
    SpaceCurationAction,
    SpaceMembership,
    SpaceMembershipAction,
    SpacePost,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="pin_owner", email="pin-owner@example.com", password="hash")
        moderator = User(username="pin_moderator", email="pin-moderator@example.com", password="hash")
        member = User(username="pin_member", email="pin-member@example.com", password="hash")
        db.session.add_all([owner, moderator, member])
        db.session.flush()

        space = Space(
            slug="pin-space",
            name="Pin Space",
            description="Space-local conversation curation.",
            owner_id=owner.id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=moderator.id, role="moderator"),
            SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
        ])

        old = Tweet(
            content="Older important conversation",
            user_id=member.id,
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
        )
        new = Tweet(
            content="Newer ordinary conversation",
            user_id=member.id,
            timestamp=datetime(2026, 2, 1, 12, 0, 0),
        )
        hidden = Tweet(
            content="Hidden conversation",
            user_id=member.id,
            timestamp=datetime(2026, 3, 1, 12, 0, 0),
        )
        removed = Tweet(
            content="Removed conversation",
            user_id=member.id,
            timestamp=datetime(2026, 4, 1, 12, 0, 0),
            is_removed=True,
        )
        db.session.add_all([old, new, hidden, removed])
        db.session.flush()

        old_row = SpacePost(space_id=space.id, tweet_id=old.id)
        new_row = SpacePost(space_id=space.id, tweet_id=new.id)
        hidden_row = SpacePost(space_id=space.id, tweet_id=hidden.id, is_hidden=True)
        removed_row = SpacePost(space_id=space.id, tweet_id=removed.id)
        db.session.add_all([old_row, new_row, hidden_row, removed_row])
        db.session.commit()

        return {
            "space": space.id,
            "slug": space.slug,
            "owner": owner.id,
            "moderator": moderator.id,
            "member": member.id,
            "old_row": old_row.id,
            "new_row": new_row.id,
            "hidden_row": hidden_row.id,
            "removed_row": removed_row.id,
            "old_tweet": old.id,
        }


def test_owner_can_pin_and_pinned_post_orders_first_without_mutating_tweet(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    with app.app_context():
        tweet = db.session.get(Tweet, ids["old_tweet"])
        original_timestamp = tweet.timestamp
        original_content = tweet.content

    response = client.post(f"/spaces/{ids['slug']}/posts/{ids['old_row']}/pin")
    assert response.status_code == 302

    with app.app_context():
        row = db.session.get(SpacePost, ids["old_row"])
        tweet = db.session.get(Tweet, ids["old_tweet"])
        assert row.pinned_at is not None
        assert row.pinned_by_id == ids["owner"]
        assert tweet.timestamp == original_timestamp
        assert tweet.content == original_content

    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert page.data.index(b"Older important conversation") < page.data.index(
        b"Newer ordinary conversation"
    )
    assert b"Pinned in this Space" in page.data


def test_moderator_can_pin_and_unpin_with_separate_curation_audit(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])

    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['old_row']}/pin"
    ).status_code == 302
    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['old_row']}/unpin"
    ).status_code == 302

    with app.app_context():
        row = db.session.get(SpacePost, ids["old_row"])
        assert row.pinned_at is None
        assert row.pinned_by_id is None
        actions = SpaceCurationAction.query.filter_by(
            space_id=ids["space"],
            space_post_id=ids["old_row"],
        ).order_by(SpaceCurationAction.id.asc()).all()
        assert [action.action_type for action in actions] == ["pin_post", "unpin_post"]
        assert SpaceMembershipAction.query.filter_by(space_id=ids["space"]).count() == 0


def test_regular_member_cannot_pin_or_unpin(client, app):
    ids = _fixture(app)
    _login(client, ids["member"])

    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['old_row']}/pin"
    ).status_code == 403
    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['old_row']}/unpin"
    ).status_code == 403


def test_hidden_and_removed_space_posts_cannot_be_pinned(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['hidden_row']}/pin"
    ).status_code == 409
    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['removed_row']}/pin"
    ).status_code == 409


def test_archived_space_blocks_pin_and_unpin_mutations(client, app):
    ids = _fixture(app)
    with app.app_context():
        space = db.session.get(Space, ids["space"])
        row = db.session.get(SpacePost, ids["old_row"])
        row.pinned_at = space.created_at
        row.pinned_by_id = ids["owner"]
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["owner"])
    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['new_row']}/pin"
    ).status_code == 409
    assert client.post(
        f"/spaces/{ids['slug']}/posts/{ids['old_row']}/unpin"
    ).status_code == 409

    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert b"Pinned in this Space" in page.data
    assert b">Unpin<" not in page.data
    assert b">Pin<" not in page.data


def test_pin_controls_are_operator_only_but_pin_label_is_readable(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    client.post(f"/spaces/{ids['slug']}/posts/{ids['old_row']}/pin")

    _login(client, ids["member"])
    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert b"Pinned in this Space" in page.data
    assert b">Unpin<" not in page.data
    assert b">Pin<" not in page.data


def test_operator_dashboard_shows_curation_audit(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])
    client.post(f"/spaces/{ids['slug']}/posts/{ids['old_row']}/pin")

    page = client.get(f"/spaces/{ids['slug']}/operator")
    assert page.status_code == 200
    assert b"Recent conversation curation" in page.data
    assert b"Pin Post" in page.data
    assert b"pin_moderator" in page.data
