"""Measured creator-support analytics for Sprint 15.

Only page visits Ripple can actually observe are recorded here. Revenue,
payments, supporters, and active memberships are intentionally absent until
those product capabilities exist.
"""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db

SUPPORT_PAGE = "support"
MEMBERSHIP_PAGE = "membership"
PAGE_TYPES = {SUPPORT_PAGE, MEMBERSHIP_PAGE}


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class SustainabilityPageVisit(db.Model):
    __tablename__ = "sustainability_page_visit"
    __table_args__ = (
        db.UniqueConstraint(
            "creator_user_id",
            "page_type",
            "visitor_key",
            "visit_date",
            name="uq_sustainability_page_visit_daily_visitor",
        ),
        db.CheckConstraint(
            "page_type in ('support', 'membership')",
            name="ck_sustainability_page_visit_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    creator_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    page_type = db.Column(db.String(20), nullable=False)
    visitor_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    visitor_key = db.Column(db.String(80), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    first_seen_at = db.Column(db.DateTime, nullable=False, default=_utcnow)


def build_sustainability_summary(creator_user_id, *, days=30):
    days = max(1, min(int(days), 90))
    end_date = datetime.now(UTC).date()
    start_date = end_date - timedelta(days=days - 1)
    rows = SustainabilityPageVisit.query.filter(
        SustainabilityPageVisit.creator_user_id == creator_user_id,
        SustainabilityPageVisit.visit_date >= start_date,
        SustainabilityPageVisit.visit_date <= end_date,
    ).all()

    totals = {SUPPORT_PAGE: 0, MEMBERSHIP_PAGE: 0}
    daily = []
    by_day = {}
    for row in rows:
        totals[row.page_type] += 1
        by_day.setdefault(row.visit_date, {SUPPORT_PAGE: 0, MEMBERSHIP_PAGE: 0})[row.page_type] += 1
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        counts = by_day.get(day, {SUPPORT_PAGE: 0, MEMBERSHIP_PAGE: 0})
        daily.append({"date": day, "support": counts[SUPPORT_PAGE], "membership": counts[MEMBERSHIP_PAGE]})

    return {
        "days": days,
        "range_start": start_date,
        "range_end": end_date,
        "support_page_visitors": totals[SUPPORT_PAGE],
        "membership_page_visitors": totals[MEMBERSHIP_PAGE],
        "daily": daily,
        "revenue_available": False,
        "supporter_count_available": False,
        "membership_count_available": False,
    }


__all__ = [
    "MEMBERSHIP_PAGE",
    "PAGE_TYPES",
    "SUPPORT_PAGE",
    "SustainabilityPageVisit",
    "build_sustainability_summary",
]
