"""Sprint 33 Story 33.1 Space announcement coverage."""

from datetime import timedelta

from twitclone.extensions import db
from twitclone.models import Notification, User
from twitclone.spaces.models import Space, SpaceAnnouncement, SpaceMembership


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app, *, visibility="public"):
    with app.app_context():
        owner = User(username="announce_owner", email="announce-owner@example.com", password="hash")
        moderator = User(
            username="announce_moderator",
            email="announce-moderator@example.com",
            password="hash",
        )
        member = User(username="announce_member", email="announce-member@example.com", password="hash")
        outsider = User(
            username="announce_outsider",
            email="announce-outsider@example.com",
            password="hash",
        )
        db.session.add_all([owner, moderator, member, outsider])
        db.session.flush()

        space = Space(
            slug="announcement-space",
            name="Announcement Space",
            description="Operator announcement coverage.",
            owner_id=owner.id,
            visibility=visibility,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all(
            [
                SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
                SpaceMembership(space_id=space.id, user_id=moderator.id, role="moderator"),
                SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
            ]
        )
        db.session.commit()
        return {
            "slug": space.slug,
            "space_id": space.id,
            "owner": owner.id,
            "moderator": moderator.id,
            "member": member.id,
            "outsider": outsider.id,
        }


def _publish(client, slug, *, title="Schedule update", body="Saturday meetup starts at 10 AM."):
    return client.post(
        f"/spaces/{slug}/announcements",
        data={"title": title, "body": body},
    )


def test_owner_and_moderator_can_publish_member_announcements(client, app):
    ids = _fixture(app)

    _login(client, ids["owner"])
    owner_response = _publish(client, ids["slug"])
    assert owner_response.status_code == 302

    _login(client, ids["moderator"])
    moderator_response = _publish(
        client,
        ids["slug"],
        title="Volunteer reminder",
        body="Please confirm your shift before Friday.",
    )
    assert moderator_response.status_code == 302

    with app.app_context():
        rows = SpaceAnnouncement.query.order_by(SpaceAnnouncement.id.asc()).all()
        assert [row.title for row in rows] == ["Schedule update", "Volunteer reminder"]
        assert [row.author_id for row in rows] == [ids["owner"], ids["moderator"]]


def test_regular_member_and_anonymous_user_cannot_publish_announcements(client, app):
    ids = _fixture(app)

    _login(client, ids["member"])
    assert _publish(client, ids["slug"]).status_code == 403

    with client.session_transaction() as session:
        session.clear()
    response = _publish(client, ids["slug"])
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_announcement_validation_is_bounded(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    assert _publish(client, ids["slug"], title="", body="body").status_code == 400
    assert _publish(client, ids["slug"], title="x" * 121, body="body").status_code == 400
    assert _publish(client, ids["slug"], title="title", body="").status_code == 400
    assert _publish(client, ids["slug"], title="title", body="x" * 1001).status_code == 400

    with app.app_context():
        assert SpaceAnnouncement.query.count() == 0


def test_announcements_are_visible_to_members_but_not_public_outsiders(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _publish(client, ids["slug"])

    _login(client, ids["member"])
    member_page = client.get(f"/spaces/{ids['slug']}")
    assert member_page.status_code == 200
    assert b"Schedule update" in member_page.data
    assert b"Saturday meetup starts at 10 AM." in member_page.data

    _login(client, ids["outsider"])
    outsider_page = client.get(f"/spaces/{ids['slug']}")
    assert outsider_page.status_code == 200
    assert b"Schedule update" not in outsider_page.data
    assert b"Announcements" not in outsider_page.data


def test_archived_space_preserves_existing_announcements_but_blocks_new_ones(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _publish(client, ids["slug"], title="Before archive", body="Historical member notice.")

    with app.app_context():
        space = db.session.get(Space, ids["space_id"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    blocked = _publish(client, ids["slug"], title="After archive", body="Should not publish.")
    assert blocked.status_code == 409

    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert b"Before archive" in page.data
    assert b"After archive" not in page.data


def test_announcements_are_newest_first_and_bounded_on_detail(client, app):
    ids = _fixture(app)
    with app.app_context():
        space = db.session.get(Space, ids["space_id"])
        owner = db.session.get(User, ids["owner"])
        first = SpaceAnnouncement(
            space_id=space.id,
            author_id=owner.id,
            title="Older",
            body="Older body",
        )
        second = SpaceAnnouncement(
            space_id=space.id,
            author_id=owner.id,
            title="Newer",
            body="Newer body",
        )
        db.session.add_all([first, second])
        db.session.flush()
        first.created_at = second.created_at - timedelta(minutes=1)
        db.session.commit()

    _login(client, ids["member"])
    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert page.data.index(b"Newer") < page.data.index(b"Older")


def test_publishing_announcement_does_not_fan_out_notifications(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])

    with app.app_context():
        before = Notification.query.count()

    response = _publish(client, ids["slug"])
    assert response.status_code == 302

    with app.app_context():
        assert Notification.query.count() == before
        assert SpaceAnnouncement.query.count() == 1
