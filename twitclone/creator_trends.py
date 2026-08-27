"""Daily Creator Pro trend series built only from persisted Ripple measurements."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from twitclone.analytics_models import PostImpression, ProfileVisit
from twitclone.models import Quote, Retweet, Tweet


def build_daily_trends(user_id: int, start, end):
    """Return one measured row per day in the selected analytics window."""
    impressions = Counter(
        item.impression_date
        for item in PostImpression.query.filter(
            PostImpression.author_id == user_id,
            PostImpression.impression_date >= start,
            PostImpression.impression_date <= end,
        ).all()
    )
    profile_visits = Counter(
        item.visit_date
        for item in ProfileVisit.query.filter(
            ProfileVisit.profile_user_id == user_id,
            ProfileVisit.visit_date >= start,
            ProfileVisit.visit_date <= end,
        ).all()
    )

    tweet_ids = [item.id for item in Tweet.query.filter_by(user_id=user_id, is_removed=False).all()]
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time())
    engagements = Counter()
    if tweet_ids:
        for item in Retweet.query.filter(
            Retweet.tweet_id.in_(tweet_ids),
            Retweet.timestamp >= start_dt,
            Retweet.timestamp < end_dt,
        ).all():
            engagements[item.timestamp.date()] += 1
        for item in Quote.query.filter(
            Quote.tweet_id.in_(tweet_ids),
            Quote.is_removed.is_(False),
            Quote.timestamp >= start_dt,
            Quote.timestamp < end_dt,
        ).all():
            engagements[item.timestamp.date()] += 1

    rows = []
    cursor = start
    while cursor <= end:
        rows.append(
            {
                "date": cursor,
                "impressions": impressions[cursor],
                "profile_visits": profile_visits[cursor],
                "engagements": engagements[cursor],
            }
        )
        cursor += timedelta(days=1)

    maxima = {
        "impressions": max((row["impressions"] for row in rows), default=0),
        "profile_visits": max((row["profile_visits"] for row in rows), default=0),
        "engagements": max((row["engagements"] for row in rows), default=0),
    }
    for row in rows:
        for metric, maximum in maxima.items():
            row[f"{metric}_pct"] = round((row[metric] / maximum) * 100, 1) if maximum else 0

    return {"rows": rows, "maxima": maxima}


__all__ = ["build_daily_trends"]
