"""Sprint 15 Story 15.5 sustainability integrity boundary coverage."""

from twitclone.creator_memberships import CreatorMembershipOffering
from twitclone.creator_support import CreatorSupportProfile
from twitclone.sustainability_analytics import SustainabilityPageVisit, build_sustainability_summary


def _column_names(model):
    return {column.name for column in model.__table__.columns}


def test_support_profile_does_not_store_financial_or_entitlement_state():
    assert _column_names(CreatorSupportProfile) == {
        "id",
        "user_id",
        "enabled",
        "message",
        "created_at",
        "updated_at",
    }


def test_membership_offering_remains_descriptive_not_enrollment_state():
    assert _column_names(CreatorMembershipOffering) == {
        "id",
        "user_id",
        "enabled",
        "name",
        "description",
        "benefits",
        "created_at",
        "updated_at",
    }


def test_sustainability_analytics_store_measured_visits_only():
    assert _column_names(SustainabilityPageVisit) == {
        "id",
        "creator_user_id",
        "page_type",
        "visitor_user_id",
        "visitor_key",
        "visit_date",
        "first_seen_at",
    }


def test_summary_keeps_unmeasured_financial_metrics_unavailable(app):
    with app.app_context():
        summary = build_sustainability_summary(999999, days=7)

    assert summary["revenue_available"] is False
    assert summary["supporter_count_available"] is False
    assert summary["membership_count_available"] is False
    assert "revenue" not in summary
    assert "conversion_rate" not in summary
    assert "payouts" not in summary
    assert "lifetime_value" not in summary
