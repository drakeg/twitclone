"""Creator Pro billing and measured analytics regression coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.analytics_models import FollowerSnapshot, PostImpression, ProfileVisit
from twitclone.billing import ensure_default_plans, grant_entitlement
from twitclone.extensions import db
from twitclone.models import Plan, Quote, Retweet, Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_creator_pro_plans_are_seeded(app):
    with app.app_context():
        ensure_default_plans()
        monthly = Plan.query.filter_by(key='creator_pro_monthly').one()
        yearly = Plan.query.filter_by(key='creator_pro_yearly').one()
        assert monthly.amount_cents == 999
        assert yearly.amount_cents == 9999
        assert monthly.entitlement_key == 'creator_pro'


def test_creator_analytics_requires_entitlement(app, client):
    with app.app_context():
        user = User(username='creatorfree', email='creatorfree@example.com', password='hash')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    _login(client, user_id)
    response = client.get('/creator/analytics', follow_redirects=False)
    assert response.status_code == 302
    assert '/billing' in response.headers['Location']


def test_creator_analytics_uses_measured_range_data_and_insights(app, client):
    today = datetime.now(UTC).date()
    now = datetime.now(UTC).replace(tzinfo=None)
    with app.app_context():
        creator = User(username='creatorpro', email='creatorpro@example.com', password='hash')
        fan = User(username='fan', email='fan@example.com', password='hash')
        other = User(username='otherfan', email='otherfan@example.com', password='hash')
        db.session.add_all([creator, fan, other])
        db.session.commit()
        grant_entitlement(creator, 'creator_pro', source='admin')
        strong = Tweet(content='Testing #Travel #RV', user_id=creator.id, timestamp=now - timedelta(days=2))
        baseline = Tweet(content='General update #News', user_id=creator.id, timestamp=now - timedelta(days=3))
        db.session.add_all([strong, baseline])
        db.session.commit()

        db.session.add_all([
            PostImpression(tweet_id=strong.id, author_id=creator.id, viewer_user_id=fan.id, viewer_key=f'user:{fan.id}', impression_date=today - timedelta(days=2)),
            PostImpression(tweet_id=strong.id, author_id=creator.id, viewer_user_id=other.id, viewer_key=f'user:{other.id}', impression_date=today - timedelta(days=1)),
            PostImpression(tweet_id=baseline.id, author_id=creator.id, viewer_user_id=fan.id, viewer_key='baseline:1', impression_date=today - timedelta(days=2)),
            PostImpression(tweet_id=baseline.id, author_id=creator.id, viewer_user_id=other.id, viewer_key='baseline:2', impression_date=today - timedelta(days=1)),
            ProfileVisit(profile_user_id=creator.id, visitor_user_id=fan.id, visitor_key=f'user:{fan.id}', visit_date=today - timedelta(days=1)),
            FollowerSnapshot(user_id=creator.id, snapshot_date=today - timedelta(days=8), follower_count=3),
            FollowerSnapshot(user_id=creator.id, snapshot_date=today - timedelta(days=1), follower_count=5),
            Retweet(user_id=fan.id, tweet_id=strong.id, timestamp=now - timedelta(days=1)),
            Quote(user_id=other.id, tweet_id=strong.id, content='Useful', timestamp=now - timedelta(days=1)),
        ])
        db.session.commit()
        creator_id = creator.id

    _login(client, creator_id)
    response = client.get('/creator/analytics?days=7')
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'Creator Pro Analytics' in text
    assert 'Testing #Travel #RV' in text
    assert '#travel' in text
    assert '#rv' in text
    assert 'Impressions' in text
    assert 'Profile visits' in text
    assert 'Engagement rate' in text
    assert 'Follower growth' in text
    assert 'Performance insights' in text
    assert 'What Ripple sees' in text
    assert 'Top measured posts' in text
    assert 'Top measured hashtags' in text
    assert 'Above average' in text
    assert 'posts/week' in text
    assert '#travel posts are outperforming your measured average' in text
    assert 'Partial history' not in text


def test_creator_analytics_marks_incomplete_history_and_defaults_invalid_range(app, client):
    today = datetime.now(UTC).date()
    with app.app_context():
        creator = User(username='newcreator', email='newcreator@example.com', password='hash')
        viewer = User(username='viewer', email='viewer@example.com', password='hash')
        db.session.add_all([creator, viewer])
        db.session.commit()
        grant_entitlement(creator, 'creator_pro', source='admin')
        tweet = Tweet(content='Fresh post', user_id=creator.id)
        db.session.add(tweet)
        db.session.commit()
        db.session.add(PostImpression(tweet_id=tweet.id, author_id=creator.id, viewer_user_id=viewer.id, viewer_key=f'user:{viewer.id}', impression_date=today))
        db.session.commit()
        creator_id = creator.id

    _login(client, creator_id)
    response = client.get('/creator/analytics?days=999')
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert '30 days' in text
    assert 'Partial history.' in text
    assert 'A complete previous 30-day window is not available yet.' in text
    assert 'Posts need measured impressions before Ripple can identify reliable performance patterns.' not in text


def test_creator_insights_do_not_make_unmeasured_performance_claims(app, client):
    with app.app_context():
        creator = User(username='quietcreator', email='quietcreator@example.com', password='hash')
        db.session.add(creator)
        db.session.commit()
        grant_entitlement(creator, 'creator_pro', source='admin')
        db.session.add(Tweet(content='No measured traffic #Topic', user_id=creator.id))
        db.session.commit()
        creator_id = creator.id

    _login(client, creator_id)
    text = client.get('/creator/analytics?days=7').get_data(as_text=True)
    assert 'Posts need measured impressions before Ripple can identify reliable performance patterns.' in text
    assert 'outperforming your measured average' not in text
    assert 'Top measured posts' not in text
