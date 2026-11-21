"""Sprint 34 Story 34.1 Space event coverage."""

from datetime import datetime

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import (
    Space,
    SpaceEvent,
    SpaceEventAction,
    SpaceEventRsvp,
    SpaceMembership,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="event_owner", email="event-owner@example.com", password="hash")
        moderator = User(
            username="event_moderator",
            email="event-moderator@example.com",
            password="hash",
        )
        member = User(username="event_member", email="event-member@example.com", password="hash")
        outsider = User(username="event_outsider", email="event-outsider@example.com", password="hash")
        db.session.add_all([owner, moderator, member, outsider])
        db.session.flush()
        space = Space(
            slug="event-space",
            name="Event Space",
            description="Space event coverage.",
            owner_id=owner.id,
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


def _create(
    client,
    slug,
    *,
    title="Monthly meetup",
    description="Bring project updates.",
    location="Community room",
    starts_at="2030-06-15T10:00",
    timezone="America/New_York",
):
    return client.post(
        f"/spaces/{slug}/events",
        data={
            "title": title,
            "description": description,
            "location": location,
            "starts_at": starts_at,
            "timezone": timezone,
        },
    )


def test_owner_and_moderator_can_create_timezone_explicit_events(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    assert _create(client, ids["slug"]).status_code == 302

    _login(client, ids["moderator"])
    assert _create(
        client,
        ids["slug"],
        title="Volunteer night",
        starts_at="2030-06-16T18:30",
    ).status_code == 302

    with app.app_context():
        rows = SpaceEvent.query.order_by(SpaceEvent.id.asc()).all()
        assert len(rows) == 2
        assert rows[0].timezone == "America/New_York"
        assert rows[0].starts_at == datetime(2030, 6, 15, 14, 0)
        assert rows[0].created_by_id == ids["owner"]
        assert rows[1].created_by_id == ids["moderator"]


def test_regular_member_and_anonymous_user_cannot_create_events(client, app):
    ids = _fixture(app)
    _login(client, ids["member"])
    assert _create(client, ids["slug"]).status_code == 403

    with client.session_transaction() as session:
        session.clear()
    response = _create(client, ids["slug"])
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_event_validation_rejects_invalid_timezone_and_dst_edge_times(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    assert _create(
        client,
        ids["slug"],
        timezone="Not/A_Zone",
    ).status_code == 400
    assert _create(
        client,
        ids["slug"],
        starts_at="2027-03-14T02:30",
        timezone="America/New_York",
    ).status_code == 400
    assert _create(
        client,
        ids["slug"],
        starts_at="2027-11-07T01:30",
        timezone="America/New_York",
    ).status_code == 400

    with app.app_context():
        assert SpaceEvent.query.count() == 0


def test_event_validation_is_bounded_and_future_only(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    assert _create(client, ids["slug"], title="").status_code == 400
    assert _create(client, ids["slug"], title="x" * 121).status_code == 400
    assert _create(client, ids["slug"], description="").status_code == 400
    assert _create(client, ids["slug"], description="x" * 1001).status_code == 400
    assert _create(client, ids["slug"], location="x" * 201).status_code == 400
    assert _create(client, ids["slug"], starts_at="2020-01-01T10:00").status_code == 400


def test_events_are_member_only_and_render_in_explicit_timezone(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    _login(client, ids["member"])
    member_page = client.get(f"/spaces/{ids['slug']}")
    assert member_page.status_code == 200
    assert b"Monthly meetup" in member_page.data
    assert b"2030-06-15 10:00" in member_page.data
    assert b"America/New_York" in member_page.data
    assert b"Community room" in member_page.data

    _login(client, ids["outsider"])
    outsider_page = client.get(f"/spaces/{ids['slug']}")
    assert outsider_page.status_code == 200
    assert b"Monthly meetup" not in outsider_page.data
    assert b"Upcoming events" not in outsider_page.data


def test_archived_space_keeps_existing_events_readable_but_blocks_new_ones(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        space = db.session.get(Space, ids["space_id"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    assert _create(
        client,
        ids["slug"],
        title="Blocked event",
        starts_at="2030-06-20T12:00",
    ).status_code == 409

    _login(client, ids["member"])
    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert b"Monthly meetup" in page.data
    assert b"Blocked event" not in page.data


def test_upcoming_events_are_chronological_and_bounded(client, app):
    ids = _fixture(app)
    with app.app_context():
        for index in range(25):
            db.session.add(
                SpaceEvent(
                    space_id=ids["space_id"],
                    created_by_id=ids["owner"],
                    title=f"Event {index:02d}",
                    description="Event body",
                    starts_at=datetime(2030, 7, 1, 12, index),
                    timezone="UTC",
                )
            )
        db.session.commit()

    _login(client, ids["member"])
    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert b"Event 00" in page.data
    assert b"Event 19" in page.data
    assert b"Event 20" not in page.data
    assert page.data.index(b"Event 00") < page.data.index(b"Event 01")


def test_operator_can_edit_event_and_preserve_prior_values_in_audit(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    response = client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/edit",
        data={
            "title": "Updated meetup",
            "description": "Updated agenda.",
            "location": "Library",
            "starts_at": "2030-06-15T11:30",
            "timezone": "America/New_York",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        event = db.session.get(SpaceEvent, event_id)
        assert event.title == "Updated meetup"
        assert event.description == "Updated agenda."
        assert event.location == "Library"
        assert event.starts_at == datetime(2030, 6, 15, 15, 30)
        assert event.updated_at is not None
        action = SpaceEventAction.query.filter_by(
            event_id=event_id,
            action_type="edited",
        ).one()
        assert action.previous_title == "Monthly meetup"
        assert action.new_title == "Updated meetup"
        assert action.previous_location == "Community room"
        assert action.new_location == "Library"


def test_cancel_hides_event_from_members_but_not_operators(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    response = client.post(f"/spaces/{ids['slug']}/events/{event_id}/cancel")
    assert response.status_code == 302

    _login(client, ids["member"])
    member_page = client.get(f"/spaces/{ids['slug']}")
    assert b"Monthly meetup" not in member_page.data

    _login(client, ids["moderator"])
    operator_page = client.get(f"/spaces/{ids['slug']}")
    assert b"Monthly meetup" in operator_page.data
    assert b"Canceled" in operator_page.data
    assert b"Restore event" in operator_page.data

    with app.app_context():
        event = db.session.get(SpaceEvent, event_id)
        assert event.is_canceled is True
        assert event.canceled_at is not None
        assert SpaceEventAction.query.filter_by(
            event_id=event_id,
            action_type="canceled",
        ).count() == 1


def test_operator_can_restore_future_canceled_event(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    client.post(f"/spaces/{ids['slug']}/events/{event_id}/cancel")
    response = client.post(f"/spaces/{ids['slug']}/events/{event_id}/restore")
    assert response.status_code == 302

    _login(client, ids["member"])
    page = client.get(f"/spaces/{ids['slug']}")
    assert b"Monthly meetup" in page.data

    with app.app_context():
        event = db.session.get(SpaceEvent, event_id)
        assert event.is_canceled is False
        assert event.canceled_at is None
        assert event.canceled_by_id is None


def test_regular_member_cannot_edit_cancel_or_restore_events(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    _login(client, ids["member"])
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/edit",
        data={
            "title": "Nope",
            "description": "Nope",
            "location": "",
            "starts_at": "2030-06-15T10:00",
            "timezone": "UTC",
        },
    ).status_code == 403
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/cancel"
    ).status_code == 403
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/restore"
    ).status_code == 403


def test_archived_space_blocks_event_lifecycle_writes(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id
        space = db.session.get(Space, ids["space_id"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/edit",
        data={
            "title": "Blocked",
            "description": "Blocked",
            "location": "",
            "starts_at": "2030-06-15T10:00",
            "timezone": "UTC",
        },
    ).status_code == 409
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/cancel"
    ).status_code == 409
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/restore"
    ).status_code == 409


def test_operator_detail_shows_event_audit_history(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/edit",
        data={
            "title": "Edited event",
            "description": "Edited description",
            "location": "Edited place",
            "starts_at": "2030-06-15T11:00",
            "timezone": "America/New_York",
        },
    )
    client.post(f"/spaces/{ids['slug']}/events/{event_id}/cancel")

    page = client.get(f"/spaces/{ids['slug']}")
    assert page.status_code == 200
    assert b"Event audit history" in page.data
    assert b'data-event-action="edited"' in page.data
    assert b'data-event-action="canceled"' in page.data


def test_member_can_set_change_and_clear_event_rsvp(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    _login(client, ids["member"])
    going = client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "going"},
    )
    assert going.status_code == 302
    with app.app_context():
        row = SpaceEventRsvp.query.one()
        assert row.status == "going"
        assert row.user_id == ids["member"]

    maybe = client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "maybe"},
    )
    assert maybe.status_code == 302
    with app.app_context():
        rows = SpaceEventRsvp.query.all()
        assert len(rows) == 1
        assert rows[0].status == "maybe"

    clear = client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "clear"},
    )
    assert clear.status_code == 302
    with app.app_context():
        assert SpaceEventRsvp.query.count() == 0


def test_rsvp_summary_is_aggregate_only_and_member_specific(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    _login(client, ids["member"])
    client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "going"},
    )
    member_page = client.get(f"/spaces/{ids['slug']}")
    assert b"1 going" in member_page.data
    assert b"0 maybe" in member_page.data
    rsvp_fragment = (
        member_page.data
        .split(b'data-event-rsvp-summary="', 1)[1]
        .split(b"</div>", 1)[0]
    )
    assert b"event_member" not in rsvp_fragment
    assert b"event-member@example.com" not in rsvp_fragment
    assert b"Clear RSVP" in rsvp_fragment

    _login(client, ids["moderator"])
    moderator_page = client.get(f"/spaces/{ids['slug']}")
    assert b"1 going" in moderator_page.data
    assert b"Clear RSVP" not in moderator_page.data


def test_nonmember_cannot_rsvp(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    _login(client, ids["outsider"])
    response = client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "going"},
    )
    assert response.status_code == 403
    with app.app_context():
        assert SpaceEventRsvp.query.count() == 0


def test_invalid_canceled_and_archived_rsvps_are_rejected(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])
    _create(client, ids["slug"])

    with app.app_context():
        event_id = SpaceEvent.query.one().id

    _login(client, ids["member"])
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "yes"},
    ).status_code == 400

    _login(client, ids["owner"])
    client.post(f"/spaces/{ids['slug']}/events/{event_id}/cancel")
    _login(client, ids["member"])
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "going"},
    ).status_code == 409

    _login(client, ids["owner"])
    client.post(f"/spaces/{ids['slug']}/events/{event_id}/restore")
    with app.app_context():
        space = db.session.get(Space, ids["space_id"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()
    _login(client, ids["member"])
    assert client.post(
        f"/spaces/{ids['slug']}/events/{event_id}/rsvp",
        data={"status": "maybe"},
    ).status_code == 409


def test_event_creation_does_not_precreate_rsvp_rows(client, app):
    ids = _fixture(app)
    _login(client, ids["moderator"])

    assert _create(client, ids["slug"]).status_code == 302
    with app.app_context():
        assert SpaceEvent.query.count() == 1
        assert SpaceEventRsvp.query.count() == 0
