"""Regression coverage for the first Ripple+ premium feature bundle."""

from datetime import UTC, datetime, timedelta

from twitclone.billing import ensure_default_plans, grant_entitlement
from twitclone.extensions import db
from twitclone.models import Entitlement, Subscription, Tweet, User


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f'{username}@example.com', password='hash')
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _schedule_parts(days):
    target = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=days)
    return target.strftime('%Y-%m-%d'), target.strftime('%H:%M')


def test_ripple_plus_plans_are_available_without_identity_verification(client, app):
    user_id = _user(app, 'plusbuyer')
    _login(client, user_id)
    response = client.get('/billing')
    assert response.status_code == 200
    assert b'Ripple+' in response.data
    assert b'$4.99' in response.data
    annual = client.get('/billing?interval=year')
    assert b'$49.99' in annual.data


def test_free_account_schedule_is_limited_to_seven_days(client, app):
    user_id = _user(app, 'freeuser')
    _login(client, user_id)
    scheduled_date, scheduled_time = _schedule_parts(30)
    response = client.post('/tweet', data={'content': 'Too far away', 'scheduled_date': scheduled_date, 'scheduled_time': scheduled_time})
    assert response.status_code == 302
    with app.app_context():
        assert Tweet.query.filter_by(user_id=user_id).count() == 0


def test_ripple_plus_can_schedule_ninety_days_ahead(client, app):
    user_id = _user(app, 'plususer')
    with app.app_context():
        user = db.session.get(User, user_id)
        grant_entitlement(user, 'ripple_plus', source='admin')
        db.session.commit()
    _login(client, user_id)
    scheduled_date, scheduled_time = _schedule_parts(30)
    response = client.post('/tweet', data={'content': 'Future Ripple+ post', 'scheduled_date': scheduled_date, 'scheduled_time': scheduled_time})
    assert response.status_code == 302
    with app.app_context():
        tweet = Tweet.query.filter_by(user_id=user_id).one()
        assert tweet.scheduled_at is not None


def test_analytics_requires_ripple_plus(client, app):
    user_id = _user(app, 'analyticsfree')
    _login(client, user_id)
    response = client.get('/analytics')
    assert response.status_code == 302
    assert '/billing' in response.headers['Location']


def test_ripple_plus_analytics_render_for_entitled_user(client, app):
    user_id = _user(app, 'analyticsplus')
    with app.app_context():
        user = db.session.get(User, user_id)
        grant_entitlement(user, 'ripple_plus', source='admin')
        db.session.add(Tweet(content='Analytics test', user_id=user_id))
        db.session.commit()
    _login(client, user_id)
    response = client.get('/analytics')
    assert response.status_code == 200
    assert b'Ripple+ Analytics' in response.data
    assert b'Reposts received' in response.data


def test_stripe_webhook_can_activate_ripple_plus_for_unverified_user(client, app, monkeypatch):
    user_id = _user(app, 'plusstripe')
    with app.app_context():
        ensure_default_plans()
    app.config.update(STRIPE_WEBHOOK_SECRET='whsec_test', STRIPE_BILLING_ENABLED=True, STRIPE_SECRET_KEY='sk_test_fake')
    event = {
        'type': 'customer.subscription.updated',
        'data': {'object': {
            'id': 'sub_plus_123',
            'customer': 'cus_plus_123',
            'status': 'active',
            'current_period_start': 1787000000,
            'current_period_end': 1789678400,
            'metadata': {'ripple_user_id': str(user_id), 'ripple_plan_key': 'ripple_plus_monthly'},
        }},
    }
    monkeypatch.setattr('twitclone.payments.routes.stripe.Webhook.construct_event', lambda payload, signature, secret: event)
    response = client.post('/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'test'})
    assert response.status_code == 200
    with app.app_context():
        assert Subscription.query.filter_by(provider_subscription_id='sub_plus_123').one().status == 'active'
        assert Entitlement.query.filter_by(user_id=user_id, key='ripple_plus').one().active is True
