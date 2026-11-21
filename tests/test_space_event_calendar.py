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
