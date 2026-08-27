"""Creator Pro audience-conversion summaries built from measured Ripple activity."""

from __future__ import annotations


def build_audience_conversion(*, stats, follower_growth, days):
    """Describe the measured path from impressions to profile visits and follows."""
    impressions = stats["impressions"]
    profile_visits = stats["profile_visits"]
    follower_delta = follower_growth["growth"]

    visit_rate = round((profile_visits / impressions) * 100, 2) if impressions else None
    follow_rate = (
        round((max(follower_delta, 0) / profile_visits) * 100, 2)
        if profile_visits
        else None
    )

    observations = []
    if not impressions:
        observations.append(
            "Ripple has not measured any post impressions in this window, so audience-conversion rates are not available yet."
        )
    elif not profile_visits:
        observations.append(
            "Ripple measured post impressions but no profile visits in this window. More measured traffic is needed before drawing conclusions about profile conversion."
        )
    else:
        observations.append(
            f"{visit_rate}% of measured post impressions corresponded to daily-unique profile visits during this {days}-day window."
        )
        if follower_growth["complete"]:
            if follower_delta > 0:
                observations.append(
                    f"Net follower growth was +{follower_delta}; that equals {follow_rate}% of measured profile visits. This is a net-change ratio, not attribution of individual follows to specific visits."
                )
            elif follower_delta == 0:
                observations.append(
                    "Follower count was unchanged across the complete measurement window despite measured profile visits."
                )
            else:
                observations.append(
                    f"Follower count decreased by {abs(follower_delta)} across the complete measurement window, so Ripple does not present a positive follow-conversion rate."
                )
        else:
            observations.append(
                "A complete follower baseline is not available for this window, so Ripple is withholding the follow-conversion ratio until enough history accumulates."
            )

    return {
        "visit_rate": visit_rate,
        "follow_rate": follow_rate if follower_growth["complete"] and follower_delta > 0 else None,
        "net_follower_growth": follower_delta,
        "follower_baseline_complete": follower_growth["complete"],
        "observations": observations,
    }


__all__ = ["build_audience_conversion"]
