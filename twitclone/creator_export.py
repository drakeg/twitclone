"""CSV export helpers for Creator Pro measured analytics."""

from __future__ import annotations

import csv
from io import StringIO


def _safe_cell(value):
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def build_creator_csv(*, dashboard, daily_trends):
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["section", "date", "post_id", "content_or_tag", "impressions", "profile_visits", "reposts", "quotes", "engagements", "engagement_rate", "value"])

    stats = dashboard["stats"]
    for key in ("followers", "impressions", "profile_visits", "reposts", "quotes", "engagements", "engagement_rate"):
        writer.writerow(["summary", "", "", key, "", "", "", "", "", "", stats[key]])

    for item in daily_trends["rows"]:
        writer.writerow(["daily", item["date"].isoformat(), "", "", item["impressions"], item["profile_visits"], "", "", item["engagements"], "", ""])

    for item in dashboard["post_performance"]:
        writer.writerow([
            "post",
            item["tweet"].timestamp.date().isoformat(),
            item["tweet"].id,
            _safe_cell(item["tweet"].content),
            item["impressions"],
            "",
            item["reposts"],
            item["quotes"],
            item["engagements"],
            item["engagement_rate"],
            "",
        ])

    for item in dashboard["hashtag_performance"]:
        writer.writerow(["hashtag", "", "", _safe_cell("#" + item["tag"]), item["impressions"], "", "", "", item["engagements"], item["engagement_rate"], item["posts"]])

    return output.getvalue()


__all__ = ["build_creator_csv"]
