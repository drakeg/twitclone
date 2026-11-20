"""Sprint 29 Story 29.1 operator member roster coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import Space, SpaceMembership


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app, member_count=30):
    with app.app_context():
        owner = User(username="roster_owner", email="owner-roster@example.com", password="hash")
        moderator = User(username="roster_moderator", email="moderator-roster@example.com", password="hash")
        regular = User(username="roster_regular", email="regular-roster@example.com", password="hash")
        db.session.add_all([owner, moderator, regular])
        db.session.flush()

        space = Space(
            slug="roster-space",
            name="Roster Space",
            description="Operator member roster coverage.",
            owner_id=owner.id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=moderator.id, role="moderator"),
            SpaceMembership(space_id=space.id, user_id=regular.id, role="member"),
        ])

        extra_ids = []
        for index in range(member_count):
            user = User(
                username=f"member_{index:02d}",
                email=f"private-{index:02d}@example.com",
                password="hash",
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                SpaceMembership(space_id=space.id, user_id=user.id, role="member")
            )
            extra_ids.append(user.id)

        db.session.commit()
        return {
            "slug": space.slug,
            "owner": owner.id,
            "moderator": moderator.id,
            "regular": regular.id,
            "extra_ids": extra_ids,
        }


def test_owner_and_moderator_can_view_member_roster(client, app):
    ids = _fixture(app, member_count=2)

    _login(client, ids["owner"])
    owner_page = client.get(f"/spaces/{ids['slug']}/members")
    assert owner_page.status_code == 200
    assert b"Member roster" in owner_page.data
    assert b"roster_owner" in owner_page.data
    assert b"roster_moderator" in owner_page.data

    _login(client, ids["moderator"])
    moderator_page = client.get(f"/spaces/{ids['slug']}/members")
    assert moderator_page.status_code == 200
    assert b"Member roster" in moderator_page.data


def test_regular_member_and_anonymous_user_cannot_view_roster(client, app):
    ids = _fixture(app, member_count=1)

    _login(client, ids["regular"])
    assert client.get(f"/spaces/{ids['slug']}/members").status_code == 403

    with client.session_transaction() as session:
        session.clear()
    anonymous = client.get(f"/spaces/{ids['slug']}/members")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]


def test_roster_search_is_case_insensitive_and_does_not_expose_email(client, app):
    ids = _fixture(app, member_count=3)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?q=MEMBER_01")
    assert response.status_code == 200
    assert b"member_01" in response.data
    assert b"member_00" not in response.data
    assert b"private-01@example.com" not in response.data
    assert b'data-member-result-count="1"' in response.data


def test_roster_role_filter_limits_results(client, app):
    ids = _fixture(app, member_count=2)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?role=moderator")
    assert response.status_code == 200
    assert b"roster_moderator" in response.data
    assert b"roster_owner" not in response.data
    assert b"roster_regular" not in response.data
    assert b'data-member-result-count="1"' in response.data


def test_roster_uses_bounded_deterministic_pagination(client, app):
    ids = _fixture(app, member_count=30)
    _login(client, ids["owner"])

    first = client.get(f"/spaces/{ids['slug']}/members")
    assert first.status_code == 200
    assert b"Page 1 of 2" in first.data
    assert b"member_00" in first.data
    assert b"member_29" not in first.data

    second = client.get(f"/spaces/{ids['slug']}/members?page=2")
    assert second.status_code == 200
    assert b"Page 2 of 2" in second.data
    assert b"member_29" in second.data

    bounded = client.get(f"/spaces/{ids['slug']}/members?page=999")
    assert bounded.status_code == 200
    assert b"Page 2 of 2" in bounded.data
