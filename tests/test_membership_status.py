"""Regression coverage for membership and subscription status."""

from datetime import UTC, datetime, timedelta

from twitclone.billing import ensure_default_plans, grant_entitlement
from twitclone.extensions import db
from twitclone.models import Plan, Subscription, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id); session['_fresh'] = True


def _user(app, username='member'):
    with app.app_context():
        user = User(username=username, email=f'{username}@example.com', password='hash')
        db.session.add(user); db.session.commit(); return user.id


def test_membership_page_shows_free_account_and_upgrade_paths(client, app):
    user_id = _user(app); _login(client, user_id)
    response = client.get('/membership')
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'Membership &amp; status' in text or 'Membership & status' in text
    assert 'Free account' in text
    assert 'Ripple+' in text and 'Creator Pro' in text and 'Verified identity' in text
    assert text.count('View upgrade options') >= 2


def test_membership_page_shows_active_entitlement_benefits(client, app):
    user_id = _user(app, 'plusmember')
    with app.app_context():
        user = db.session.get(User, user_id); grant_entitlement(user, 'ripple_plus', source='admin'); db.session.commit()
    _login(client, user_id)
    text = client.get('/membership').get_data(as_text=True)
    assert '90-day scheduling' in text
    assert 'Bookmark folders' in text
    assert 'Use Ripple+ analytics' in text
    assert 'without a recurring Stripe subscription' in text


def test_membership_page_surfaces_past_due_subscription(client, app):
    user_id = _user(app, 'pastdue')
    with app.app_context():
        ensure_default_plans(); plan = Plan.query.filter_by(key='creator_pro_monthly').one()
        subscription = Subscription(user_id=user_id, plan_id=plan.id, provider='stripe', provider_customer_id='cus_test', provider_subscription_id='sub_test', status='past_due', current_period_end=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=3))
        db.session.add(subscription); db.session.commit()
    _login(client, user_id)
    text = client.get('/membership').get_data(as_text=True)
    assert 'Billing needs attention' in text
    assert 'Past due' in text
    assert 'Creator Pro' in text
    assert 'Manage billing' in text


def test_membership_page_keeps_identity_approval_separate_from_payment(client, app):
    user_id = _user(app, 'identitymember'); _login(client, user_id)
    text = client.get('/membership').get_data(as_text=True)
    assert 'Apply for verification' in text
    assert 'Paying never causes Ripple to approve an identity' in text


def test_profile_links_to_membership_status(client, app):
    user_id = _user(app, 'profilemember'); _login(client, user_id)
    text = client.get('/profile/profilemember').get_data(as_text=True)
    assert 'Membership' in text
    assert '/membership' in text
