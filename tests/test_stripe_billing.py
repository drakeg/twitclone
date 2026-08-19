"""Regression coverage for Stripe-backed verified badge billing."""

from twitclone.billing import ensure_default_plans
from twitclone.extensions import db
from twitclone.models import Entitlement, Subscription, User


def _user(app, username, *, verified=False, verification_type='person'):
    with app.app_context():
        user = User(
            username=username,
            email=f'{username}@example.com',
            password='hash',
            identity_verified=verified,
            verification_type=verification_type if verified else None,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_unverified_user_cannot_start_badge_checkout(client, app):
    user_id = _user(app, 'notverified')
    _login(client, user_id)
    response = client.post('/billing/checkout/verified_individual_monthly')
    assert response.status_code == 302
    assert '/verification/apply' in response.headers['Location']


def test_approved_identity_sees_eligible_plans_without_collecting_money(client, app):
    user_id = _user(app, 'approved', verified=True)
    _login(client, user_id)
    response = client.get('/billing')
    assert response.status_code == 200
    assert b'$2.99' in response.data
    assert b'$29.99' in response.data
    assert b'Stripe billing is disabled' in response.data


def test_verified_webhook_controls_badge_entitlement(client, app, monkeypatch):
    user_id = _user(app, 'subscriber', verified=True)
    with app.app_context():
        ensure_default_plans()

    app.config.update(STRIPE_WEBHOOK_SECRET='whsec_test', STRIPE_BILLING_ENABLED=True, STRIPE_SECRET_KEY='sk_test_fake')

    active_event = {
        'type': 'customer.subscription.updated',
        'data': {'object': {
            'id': 'sub_test_123',
            'customer': 'cus_test_123',
            'status': 'active',
            'current_period_start': 1787000000,
            'current_period_end': 1789678400,
            'metadata': {
                'ripple_user_id': str(user_id),
                'ripple_plan_key': 'verified_individual_monthly',
            },
        }},
    }
    monkeypatch.setattr('twitclone.payments.routes.stripe.Webhook.construct_event', lambda payload, signature, secret: active_event)
    response = client.post('/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'test'})
    assert response.status_code == 200

    with app.app_context():
        subscription = Subscription.query.filter_by(provider_subscription_id='sub_test_123').one()
        entitlement = Entitlement.query.filter_by(user_id=user_id, key='verified_badge').one()
        user = db.session.get(User, user_id)
        assert subscription.status == 'active'
        assert entitlement.active is True
        assert user.verified_badge_active is True

    canceled_event = {
        'type': 'customer.subscription.deleted',
        'data': {'object': {
            'id': 'sub_test_123',
            'customer': 'cus_test_123',
            'status': 'canceled',
            'metadata': {
                'ripple_user_id': str(user_id),
                'ripple_plan_key': 'verified_individual_monthly',
            },
        }},
    }
    monkeypatch.setattr('twitclone.payments.routes.stripe.Webhook.construct_event', lambda payload, signature, secret: canceled_event)
    response = client.post('/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'test'})
    assert response.status_code == 200
    with app.app_context():
        assert Subscription.query.filter_by(provider_subscription_id='sub_test_123').one().status == 'canceled'
        assert Entitlement.query.filter_by(user_id=user_id, key='verified_badge').one().active is False
        assert db.session.get(User, user_id).verified_badge_active is False
