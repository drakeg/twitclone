"""Regression coverage for the Plans & Pricing storefront."""

from twitclone.billing import grant_entitlement
from twitclone.extensions import db
from twitclone.models import User


def _user(app, username='pricing', *, verified=False):
    with app.app_context():
        user = User(username=username, email=f'{username}@example.com', password='hash', identity_verified=verified, verification_type='person' if verified else None)
        db.session.add(user); db.session.commit(); return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id); session['_fresh'] = True


def test_pricing_storefront_explains_free_and_paid_tiers(client, app):
    user_id = _user(app); _login(client, user_id)
    response = client.get('/billing')
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'Choose the Ripple that fits you' in text
    assert 'Free' in text and 'Ripple+' in text and 'Creator Pro' in text
    assert '$4.99' in text and '$9.99' in text
    assert 'Apply for verification' in text


def test_annual_toggle_shows_annual_prices(client, app):
    user_id = _user(app, 'annual'); _login(client, user_id)
    response = client.get('/billing?interval=year')
    text = response.get_data(as_text=True)
    assert '$49.99' in text
    assert '$99.99' in text
    assert '/yr' in text


def test_verified_person_sees_correct_badge_price_for_selected_interval(client, app):
    user_id = _user(app, 'verifiedpricing', verified=True); _login(client, user_id)
    monthly = client.get('/billing?interval=month').get_data(as_text=True)
    annual = client.get('/billing?interval=year').get_data(as_text=True)
    assert '$2.99' in monthly
    assert '$29.99' in annual


def test_active_entitlements_are_marked_as_current(client, app):
    user_id = _user(app, 'currentplans')
    with app.app_context():
        user = db.session.get(User, user_id); grant_entitlement(user, 'ripple_plus', source='admin'); grant_entitlement(user, 'creator_pro', source='admin'); db.session.commit()
    _login(client, user_id)
    text = client.get('/billing').get_data(as_text=True)
    assert text.count('Current plan') >= 2
    assert 'View analytics' in text
    assert 'View Creator Pro analytics' in text


def test_invalid_interval_falls_back_to_monthly(client, app):
    user_id = _user(app, 'badinterval'); _login(client, user_id)
    text = client.get('/billing?interval=weekly').get_data(as_text=True)
    assert '$4.99' in text
    assert '$9.99' in text
