"""Regression coverage for measured Creator Pro daily trend reporting."""

from datetime import UTC, datetime, timedelta

from twitclone.analytics_models import PostImpression, ProfileVisit
from twitclone.creator_trends import build_daily_trends
from twitclone.extensions import db
from twitclone.models import Quote, Retweet, Tweet, User


def test_daily_trends_fill_zero_days_and_count_measured_activity(app):
    today = datetime.now(UTC).date()
    now = datetime.now(UTC).replace(tzinfo=None)
    start = today - timedelta(days=2)
    with app.app_context():
        creator = User(username="trendcreator", email="trend@example.com", password="hash")
        viewer = User(username="trendviewer", email="viewer@example.com", password="hash")
        db.session.add_all([creator, viewer])
        db.session.commit()
        tweet = Tweet(content="Measured trend", user_id=creator.id, timestamp=now - timedelta(days=2))
        db.session.add(tweet)
        db.session.commit()
        db.session.add_all(
            [
                PostImpression(tweet_id=tweet.id, author_id=creator.id, viewer_user_id=viewer.id, viewer_key="trend:1", impression_date=start),
                PostImpression(tweet_id=tweet.id, author_id=creator.id, viewer_user_id=viewer.id, viewer_key="trend:2", impression_date=today),
                ProfileVisit(profile_user_id=creator.id, visitor_user_id=viewer.id, visitor_key="visit:1", visit_date=today),
                Retweet(user_id=viewer.id, tweet_id=tweet.id, timestamp=now),
                Quote(user_id=viewer.id, tweet_id=tweet.id, content="Quoted", timestamp=now),
            ]
        )
        db.session.commit()

        trend = build_daily_trends(creator.id, start, today)

    assert len(trend["rows"]) == 3
    assert trend["rows"][0]["impressions"] == 1
    assert trend["rows"][1] == {
        "date": start + timedelta(days=1),
        "impressions": 0,
        "profile_visits": 0,
        "engagements": 0,
        "impressions_pct": 0.0,
        "profile_visits_pct": 0.0,
        "engagements_pct": 0.0,
    }
    assert trend["rows"][2]["impressions"] == 1
    assert trend["rows"][2]["profile_visits"] == 1
    assert trend["rows"][2]["engagements"] == 2
    assert trend["maxima"] == {"impressions": 1, "profile_visits": 1, "engagements": 2}


def test_creator_dashboard_renders_accessible_daily_trend_table(app, client):
    today = datetime.now(UTC).date()
    with app.app_context():
        creator = User(username="trendpro", email="trendpro@example.com", password="hash")
        viewer = User(username="trendfan", email="trendfan@example.com", password="hash")
        db.session.add_all([creator, viewer])
        db.session.commit()
        from twitclone.billing import grant_entitlement

        grant_entitlement(creator, "creator_pro", source="admin")
        tweet = Tweet(content="Trend dashboard", user_id=creator.id)
        db.session.add(tweet)
        db.session.commit()
        db.session.add(PostImpression(tweet_id=tweet.id, author_id=creator.id, viewer_user_id=viewer.id, viewer_key="dashboard:1", impression_date=today))
        db.session.commit()
        creator_id = creator.id

    with client.session_transaction() as session:
        session["_user_id"] = str(creator_id)
        session["_fresh"] = True

    response = client.get("/creator/analytics?days=7")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Daily activity trend" in text
    assert "View exact daily counts" in text
    assert "Each series is scaled to its own highest day" in text
    assert today.strftime("%Y-%m-%d") in text
    assert "<th>Impressions</th>" in text
    assert "<th>Profile visits</th>" in text
    assert "<th>Engagements</th>" in text
