"""Sprint 15 Story 15.4 measured sustainability analytics coverage."""

from twitclone.creator_memberships import CreatorMembershipOffering
from twitclone.creator_support import CreatorSupportProfile
from twitclone.extensions import db
from twitclone.models import User
from twitclone.sustainability_analytics import SustainabilityPageVisit, build_sustainability_summary


def _users(app):
    with app.app_context():
        creator = User(username="support_analytics_creator", email="support-analytics@example.com", password="hash")
        visitor = User(username="support_analytics_visitor", email="support-visitor@example.com", password="hash")
        db.session.add_all([creator, visitor])
        db.session.flush()
        db.session.add_all([
            CreatorSupportProfile(user_id=creator.id, enabled=True, message="Support this work."),
            CreatorMembershipOffering(
                user_id=creator.id,
                enabled=True,
                name="Support Club",
                description="Future supporter benefits.",
                benefits="supporter_updates",
            ),
        ])
        db.session.commit()
        return creator.id, visitor.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_sustainability_analytics_require_authentication(client):
    response = client.get("/creator/support/analytics")
    assert response.status_code in (302, 401)


def test_public_support_and_membership_pages_record_unique_daily_visitors(client, app):
    creator_id, visitor_id = _users(app)
    _login(client, visitor_id)

    assert client.get("/support/support_analytics_creator").status_code == 200
    assert client.get("/support/support_analytics_creator").status_code == 200
    assert client.get("/support/support_analytics_creator/membership").status_code == 200
    assert client.get("/support/support_analytics_creator/membership").status_code == 200

    with app.app_context():
        rows = SustainabilityPageVisit.query.filter_by(creator_user_id=creator_id).all()
        assert len(rows) == 2
        assert {row.page_type for row in rows} == {"support", "membership"}
        assert all(row.visitor_user_id == visitor_id for row in rows)


def test_creator_self_views_are_not_counted(client, app):
    creator_id, _ = _users(app)
    _login(client, creator_id)

    assert client.get("/support/support_analytics_creator").status_code == 200
    assert client.get("/support/support_analytics_creator/membership").status_code == 200

    with app.app_context():
        assert SustainabilityPageVisit.query.filter_by(creator_user_id=creator_id).count() == 0


def test_dashboard_reports_only_measured_page_interest(client, app):
    creator_id, visitor_id = _users(app)
    _login(client, visitor_id)
    client.get("/support/support_analytics_creator")
    client.get("/support/support_analytics_creator/membership")

    _login(client, creator_id)
    response = client.get("/creator/support/analytics?days=30")
    assert response.status_code == 200
    assert b"Support analytics" in response.data
    assert b"No invented money or member metrics" in response.data
    assert b"revenue" in response.data.lower()
    assert b"active member count" in response.data.lower()

    with app.app_context():
        summary = build_sustainability_summary(creator_id, days=30)
        assert summary["support_page_visitors"] == 1
        assert summary["membership_page_visitors"] == 1
        assert summary["revenue_available"] is False
        assert summary["supporter_count_available"] is False
        assert summary["membership_count_available"] is False


def test_disabled_or_missing_public_pages_do_not_record_visits(client, app):
    creator_id, visitor_id = _users(app)
    with app.app_context():
        CreatorSupportProfile.query.filter_by(user_id=creator_id).one().enabled = False
        db.session.commit()
    _login(client, visitor_id)

    assert client.get("/support/support_analytics_creator").status_code == 404
    assert client.get("/support/support_analytics_creator/membership").status_code == 404
    with app.app_context():
        assert SustainabilityPageVisit.query.filter_by(creator_user_id=creator_id).count() == 0
