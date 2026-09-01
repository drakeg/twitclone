"""Regression coverage for moderation queue triage."""

from twitclone.extensions import db
from twitclone.models import PostReport, Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _seed_reports(client, app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", password="hash", is_admin=True)
        author = User(username="author", email="author@example.com", password="hash")
        reporter1 = User(username="reporter1", email="r1@example.com", password="hash")
        reporter2 = User(username="reporter2", email="r2@example.com", password="hash")
        db.session.add_all([admin, author, reporter1, reporter2])
        db.session.flush()
        first = Tweet(content="first reported post", user_id=author.id)
        second = Tweet(content="second reported post", user_id=author.id)
        db.session.add_all([first, second])
        db.session.flush()
        db.session.add_all([
            PostReport(reporter_id=reporter1.id, author_id=author.id, content_type="tweet", content_id=first.id, category="bullying", status="pending"),
            PostReport(reporter_id=reporter2.id, author_id=author.id, content_type="tweet", content_id=first.id, category="abuse", status="pending"),
            PostReport(reporter_id=reporter1.id, author_id=author.id, content_type="tweet", content_id=second.id, category="spam", status="dismissed"),
        ])
        db.session.commit()
        admin_id = admin.id
    _login(client, admin_id)


def test_moderation_defaults_to_pending_and_shows_summary(client, app):
    _seed_reports(client, app)

    response = client.get("/admin/moderation")

    assert response.status_code == 200
    assert b"Pending 2" in response.data
    assert b"Dismissed 1" in response.data
    assert b"first reported post" in response.data
    assert b"second reported post" not in response.data


def test_moderation_filters_by_status_and_category(client, app):
    _seed_reports(client, app)

    dismissed = client.get("/admin/moderation?status=dismissed")
    bullying = client.get("/admin/moderation?status=all&category=bullying")

    assert b"second reported post" in dismissed.data
    assert b"first reported post" not in dismissed.data
    assert b"Bullying or harassment" in bullying.data
    assert b"first reported post" in bullying.data
    assert b"second reported post" not in bullying.data


def test_moderation_highlights_multiple_reports_on_same_content(client, app):
    _seed_reports(client, app)

    response = client.get("/admin/moderation")

    assert response.data.count(b"2 reports on this content") == 2


def test_invalid_filters_fall_back_to_pending_queue(client, app):
    _seed_reports(client, app)

    response = client.get("/admin/moderation?status=bogus&category=bogus&content_type=bogus")

    assert response.status_code == 200
    assert b"first reported post" in response.data
    assert b"second reported post" not in response.data
