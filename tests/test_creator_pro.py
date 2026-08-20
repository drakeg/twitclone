"""Creator Pro billing and analytics regression coverage."""

from twitclone.billing import ensure_default_plans, grant_entitlement
from twitclone.extensions import db
from twitclone.models import Plan, Quote, Retweet, Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id); session['_fresh'] = True


def test_creator_pro_plans_are_seeded(app):
    with app.app_context():
        ensure_default_plans()
        monthly = Plan.query.filter_by(key='creator_pro_monthly').one(); yearly = Plan.query.filter_by(key='creator_pro_yearly').one()
        assert monthly.amount_cents == 999; assert yearly.amount_cents == 9999; assert monthly.entitlement_key == 'creator_pro'


def test_creator_analytics_requires_entitlement(app, client):
    with app.app_context():
        user=User(username='creatorfree',email='creatorfree@example.com',password='hash'); db.session.add(user); db.session.commit(); user_id=user.id
    _login(client,user_id); response=client.get('/creator/analytics',follow_redirects=False); assert response.status_code == 302; assert '/billing' in response.headers['Location']


def test_creator_analytics_reports_post_and_hashtag_engagement(app, client):
    with app.app_context():
        creator=User(username='creatorpro',email='creatorpro@example.com',password='hash'); fan=User(username='fan',email='fan@example.com',password='hash'); db.session.add_all([creator,fan]); db.session.commit()
        grant_entitlement(creator,'creator_pro',source='admin'); tweet=Tweet(content='Testing #Travel #RV',user_id=creator.id); db.session.add(tweet); db.session.commit(); db.session.add(Retweet(user_id=fan.id,tweet_id=tweet.id)); db.session.add(Quote(user_id=fan.id,tweet_id=tweet.id,content='Useful')); db.session.commit(); creator_id=creator.id
    _login(client,creator_id); response=client.get('/creator/analytics'); assert response.status_code == 200; text=response.get_data(as_text=True); assert 'Creator Pro Analytics' in text; assert 'Testing #Travel #RV' in text; assert '#travel' in text; assert '#rv' in text; assert 'Total engagements' in text
