"""Regression coverage for Creator Pro analytics CSV export."""

from datetime import UTC, datetime

from twitclone.analytics_models import PostImpression
from twitclone.billing import grant_entitlement
from twitclone.creator_export import build_creator_csv
from twitclone.extensions import db
from twitclone.models import Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_csv_helper_includes_sections_and_neutralizes_formula_cells():
    class FakeTweet:
        id = 9
        content = '=HYPERLINK("bad")'
        timestamp = datetime(2026, 8, 26, 12, 0)

    dashboard = {
        'stats': {'followers': 3, 'impressions': 4, 'profile_visits': 2, 'reposts': 1, 'quotes': 0, 'engagements': 1, 'engagement_rate': 25.0},
        'post_performance': [{'tweet': FakeTweet(), 'impressions': 4, 'reposts': 1, 'quotes': 0, 'engagements': 1, 'engagement_rate': 25.0}],
        'hashtag_performance': [{'tag': 'travel', 'posts': 1, 'impressions': 4, 'engagements': 1, 'engagement_rate': 25.0}],
    }
    trends = {'rows': [{'date': datetime(2026, 8, 26).date(), 'impressions': 4, 'profile_visits': 2, 'engagements': 1}]}

    payload = build_creator_csv(dashboard=dashboard, daily_trends=trends)

    assert 'summary' in payload
    assert 'daily' in payload
    assert 'post' in payload
    assert 'hashtag' in payload
    assert "'=HYPERLINK" in payload


def test_creator_export_requires_creator_pro(client, app):
    with app.app_context():
        user = User(username='freeexport', email='freeexport@example.com', password='hash')
        db.session.add(user); db.session.commit(); user_id = user.id
    _login(client, user_id)

    response = client.get('/creator/analytics/export.csv?days=7', follow_redirects=False)

    assert response.status_code == 302
    assert '/billing' in response.headers['Location']


def test_creator_export_downloads_measured_csv(client, app):
    today = datetime.now(UTC).date()
    with app.app_context():
        creator = User(username='exportcreator', email='exportcreator@example.com', password='hash')
        viewer = User(username='exportviewer', email='exportviewer@example.com', password='hash')
        db.session.add_all([creator, viewer]); db.session.commit()
        grant_entitlement(creator, 'creator_pro', source='admin')
        tweet = Tweet(content='Measured export #Travel', user_id=creator.id)
        db.session.add(tweet); db.session.commit()
        db.session.add(PostImpression(tweet_id=tweet.id, author_id=creator.id, viewer_user_id=viewer.id, viewer_key=f'user:{viewer.id}', impression_date=today))
        db.session.commit(); creator_id = creator.id
    _login(client, creator_id)

    response = client.get('/creator/analytics/export.csv?days=7')
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename="ripple-creator-analytics-' in response.headers['Content-Disposition']
    assert response.headers['Cache-Control'] == 'private, no-store'
    assert 'Measured export #Travel' in text
    assert 'daily' in text
    assert 'hashtag' in text
