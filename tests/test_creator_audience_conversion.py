"""Regression coverage for measured Creator Pro audience-conversion summaries."""

from twitclone.creator_audience import build_audience_conversion


def test_audience_conversion_reports_measured_rates_with_complete_baseline():
    result = build_audience_conversion(
        stats={"impressions": 200, "profile_visits": 20},
        follower_growth={"growth": 4, "complete": True},
        days=30,
    )

    assert result["visit_rate"] == 10.0
    assert result["follow_rate"] == 20.0
    assert result["net_follower_growth"] == 4
    assert "not attribution" in result["observations"][1]


def test_audience_conversion_withholds_follow_rate_without_complete_baseline():
    result = build_audience_conversion(
        stats={"impressions": 100, "profile_visits": 10},
        follower_growth={"growth": 3, "complete": False},
        days=7,
    )

    assert result["visit_rate"] == 10.0
    assert result["follow_rate"] is None
    assert "withholding" in result["observations"][1]


def test_audience_conversion_handles_no_impressions_without_fake_zero_rate():
    result = build_audience_conversion(
        stats={"impressions": 0, "profile_visits": 0},
        follower_growth={"growth": 0, "complete": False},
        days=30,
    )

    assert result["visit_rate"] is None
    assert result["follow_rate"] is None
    assert "not available yet" in result["observations"][0]


def test_audience_conversion_does_not_present_negative_growth_as_conversion():
    result = build_audience_conversion(
        stats={"impressions": 50, "profile_visits": 5},
        follower_growth={"growth": -2, "complete": True},
        days=30,
    )

    assert result["visit_rate"] == 10.0
    assert result["follow_rate"] is None
    assert "decreased by 2" in result["observations"][1]
