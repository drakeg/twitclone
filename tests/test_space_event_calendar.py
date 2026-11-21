"""Sprint 35 Story 35.1 Space event calendar export coverage."""

from datetime import datetime

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import Space, SpaceEvent, SpaceMembership


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(username="ical_owner", email="ical-owner@example.com", password="hash")
        member = User(username="ical_member", email="ical-member@example.com", password="hash")
        outsider = User(username="ical_outsider", email="ical-outsider@example.com", password="hash")
        db.session.add_all([owner, member, outsider])
        db.session.flush()
        space = Space(
            slug="calendar-space",
            name="Calendar, Space",
            description="Calendar export coverage.",
            owner_id=owner.id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all(
            [
                SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
                SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
            ]
        )
        db.session.commit()
        return {
            "slug": space.slug,
            "space_id": space.id,
            "owner": owner.id,
            "member": member.id,
            "outsider": outsider.id,
        }


def _event(app, ids, *, title, starts_at, description="Bring notes.", location=None, canceled=False):
    with app.app_context():
        row = SpaceEvent(
            space_id=ids["space_id"],
            created_by_id=ids["owner"],
            title=title,
            description=description,
            location=location,
            starts_at=starts_at,
            timezone="UTC",
            is_canceled=canceled,
        )
        db.session.add(row)
        db.session.commit()
        return row.id


def test_member_can_download_private_icalendar_export(client, app):
    ids = _fixture(app)
    _event(
        app,
        ids,
        title="Planning meeting",
        starts_at=datetime(2030, 6, 15, 14, 0),
        location="Room 1",
    )
    _login(client, ids["member"])

    response = client.get(f"/spaces/{ids['slug']}/events/calendar.ics")
    body = response.data.decode()

    assert response.status_code == 200
    assert response.mimetype == "text/calendar"
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="calendar-space-events.ics"'
    )
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "BEGIN:VCALENDAR\r\n" in body
    assert "BEGIN:VEVENT\r\n" in body
    assert "DTSTART:20300615T140000Z\r\n" in body
    assert "SUMMARY:Planning meeting\r\n" in body
    assert "LOCATION:Room 1\r\n" in body


def test_calendar_export_is_member_only(client, app):
    ids = _fixture(app)

    _login(client, ids["outsider"])
    assert client.get(f"/spaces/{ids['slug']}/events/calendar.ics").status_code == 403

    with client.session_transaction() as session:
        session.clear()
    anonymous = client.get(f"/spaces/{ids['slug']}/events/calendar.ics")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]


def test_calendar_export_omits_canceled_and_past_events(client, app):
    ids = _fixture(app)
    _event(app, ids, title="Upcoming", starts_at=datetime(2030, 6, 15, 14, 0))
    _event(app, ids, title="Canceled", starts_at=datetime(2030, 6, 16, 14, 0), canceled=True)
    _event(app, ids, title="Past", starts_at=datetime(2020, 6, 15, 14, 0))
    _login(client, ids["owner"])

    body = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data.decode()

    assert "SUMMARY:Upcoming" in body
    assert "SUMMARY:Canceled" not in body
    assert "SUMMARY:Past" not in body


def test_calendar_export_escapes_text_and_excludes_private_member_data(client, app):
    ids = _fixture(app)
    _event(
        app,
        ids,
        title="Planning, review; sync",
        description="Line one\nLine two \\ path",
        location="Room, A; East",
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    _login(client, ids["member"])

    body = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data.decode()

    assert "X-WR-CALNAME:Calendar\\, Space" in body
    assert "SUMMARY:Planning\\, review\\; sync" in body
    assert "DESCRIPTION:Line one\\nLine two \\\\ path" in body
    assert "LOCATION:Room\\, A\\; East" in body
    assert "ical-member@example.com" not in body
    assert "ical_owner" not in body
    assert "going" not in body.lower()
    assert "maybe" not in body.lower()


def test_calendar_export_is_chronological_and_bounded(client, app, monkeypatch):
    ids = _fixture(app)
    for index in range(4):
        _event(
            app,
            ids,
            title=f"Event {index}",
            starts_at=datetime(2030, 7, 1, 12, index),
        )
    monkeypatch.setattr("twitclone.spaces.routes._EVENT_CALENDAR_MAX_ROWS", 3)
    _login(client, ids["member"])

    body = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data.decode()

    assert body.index("SUMMARY:Event 0") < body.index("SUMMARY:Event 1")
    assert body.index("SUMMARY:Event 1") < body.index("SUMMARY:Event 2")
    assert "SUMMARY:Event 3" not in body


def test_calendar_export_folds_long_utf8_lines_to_75_octets(client, app):
    ids = _fixture(app)
    _event(
        app,
        ids,
        title="Résumé " + ("é" * 50),
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    _login(client, ids["member"])

    body = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data.decode()
    physical_lines = body.split("\r\n")

    assert any(line.startswith(" ") for line in physical_lines)
    assert all(len(line.encode("utf-8")) <= 75 for line in physical_lines if line)


def test_member_can_download_single_event_calendar(client, app):
    ids = _fixture(app)
    first_id = _event(
        app,
        ids,
        title="Selected event",
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    _event(
        app,
        ids,
        title="Other event",
        starts_at=datetime(2030, 6, 16, 14, 0),
    )
    _login(client, ids["member"])

    response = client.get(
        f"/spaces/{ids['slug']}/events/{first_id}/calendar.ics"
    )
    body = response.data.decode()

    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == (
        f'attachment; filename="calendar-space-event-{first_id}.ics"'
    )
    assert f"UID:space-event-{first_id}@ripple.local" in body
    assert "SUMMARY:Selected event" in body
    assert "SUMMARY:Other event" not in body


def test_single_event_calendar_is_member_only(client, app):
    ids = _fixture(app)
    event_id = _event(
        app,
        ids,
        title="Selected event",
        starts_at=datetime(2030, 6, 15, 14, 0),
    )

    _login(client, ids["outsider"])
    assert client.get(
        f"/spaces/{ids['slug']}/events/{event_id}/calendar.ics"
    ).status_code == 403


def test_single_event_calendar_rejects_canceled_and_past_events(client, app):
    ids = _fixture(app)
    canceled_id = _event(
        app,
        ids,
        title="Canceled",
        starts_at=datetime(2030, 6, 15, 14, 0),
        canceled=True,
    )
    past_id = _event(
        app,
        ids,
        title="Past",
        starts_at=datetime(2020, 6, 15, 14, 0),
    )
    _login(client, ids["owner"])

    assert client.get(
        f"/spaces/{ids['slug']}/events/{canceled_id}/calendar.ics"
    ).status_code == 404
    assert client.get(
        f"/spaces/{ids['slug']}/events/{past_id}/calendar.ics"
    ).status_code == 404


def test_space_event_page_exposes_single_event_calendar_control(client, app):
    ids = _fixture(app)
    event_id = _event(
        app,
        ids,
        title="Selected event",
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    _login(client, ids["member"])

    response = client.get(f"/spaces/{ids['slug']}")

    assert response.status_code == 200
    assert b"Add to calendar" in response.data
    assert f"/events/{event_id}/calendar.ics".encode() in response.data


def test_archived_space_calendar_exports_remain_available(client, app):
    ids = _fixture(app)
    event_id = _event(
        app,
        ids,
        title="Archived-space event",
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    with app.app_context():
        space = db.session.get(Space, ids["space_id"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["member"])
    full = client.get(f"/spaces/{ids['slug']}/events/calendar.ics")
    single = client.get(
        f"/spaces/{ids['slug']}/events/{event_id}/calendar.ics"
    )

    assert full.status_code == 200
    assert single.status_code == 200
    assert "SUMMARY:Archived-space event" in full.data.decode()
    assert "SUMMARY:Archived-space event" in single.data.decode()


def test_empty_space_calendar_is_valid_without_events(client, app):
    ids = _fixture(app)
    _login(client, ids["member"])

    body = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data.decode()

    assert body.startswith("BEGIN:VCALENDAR\r\n")
    assert body.endswith("END:VCALENDAR\r\n")
    assert "BEGIN:VEVENT" not in body


def test_full_and_single_exports_use_same_stable_uid(client, app):
    ids = _fixture(app)
    event_id = _event(
        app,
        ids,
        title="Stable UID event",
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    _login(client, ids["member"])

    full = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data.decode()
    single = client.get(
        f"/spaces/{ids['slug']}/events/{event_id}/calendar.ics"
    ).data.decode()
    uid = f"UID:space-event-{event_id}@ripple.local"

    assert uid in full
    assert uid in single


def test_calendar_export_succeeds_at_exact_configured_bound(client, app, monkeypatch):
    ids = _fixture(app)
    for index in range(3):
        _event(
            app,
            ids,
            title=f"Bound {index}",
            starts_at=datetime(2030, 7, 1, 12, index),
        )
    monkeypatch.setattr("twitclone.spaces.routes._EVENT_CALENDAR_MAX_ROWS", 3)
    _login(client, ids["member"])

    body = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data.decode()

    assert body.count("BEGIN:VEVENT") == 3
    assert "SUMMARY:Bound 0" in body
    assert "SUMMARY:Bound 2" in body


def test_calendar_export_uses_crlf_and_continuation_whitespace(client, app):
    ids = _fixture(app)
    _event(
        app,
        ids,
        title="Long " + ("é" * 60),
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    _login(client, ids["member"])

    payload = client.get(f"/spaces/{ids['slug']}/events/calendar.ics").data
    text = payload.decode()

    assert b"\r\n" in payload
    assert "\n " in text
    assert all(
        len(line.encode("utf-8")) <= 75
        for line in text.split("\r\n")
        if line
    )


def test_single_event_export_excludes_member_and_rsvp_identity_data(client, app):
    ids = _fixture(app)
    event_id = _event(
        app,
        ids,
        title="Private-safe event",
        starts_at=datetime(2030, 6, 15, 14, 0),
    )
    _login(client, ids["member"])

    body = client.get(
        f"/spaces/{ids['slug']}/events/{event_id}/calendar.ics"
    ).data.decode()

    assert "ical-member@example.com" not in body
    assert "ical_owner" not in body
    assert "going" not in body.lower()
    assert "maybe" not in body.lower()
