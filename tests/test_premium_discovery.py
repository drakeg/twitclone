"""Regression coverage for restrained in-context paid feature discovery."""

from twitclone.billing import grant_entitlement
from twitclone.extensions import db
from twitclone.models import User


def _user(app, username='discovery'):
    with app.app_context():
        user = User(username=username, email=f'{username}@example.com', password='hash')
        db.session.add(user); db.session.commit(); return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id); session['_fresh'] = True


def test_free_user_sees_contextual_profile_upgrade_without_losing_free_fields(client, app):
    user_id = _user(app); _login(client, user_id)
    text = client.get('/profile/edit').get_data(as_text=True)
    assert 'Username' in text and 'Email' in text and 'Bio' in text
    assert 'Included with Ripple+' in text
    assert 'five curated profile themes' in text
    assert 'Your normal profile, bio, and avatar stay free' in text


def test_ripple_plus_user_sees_real_profile_controls_not_upgrade_pitch(client, app):
    user_id = _user(app, 'plusdiscovery')
    with app.app_context():
        user = db.session.get(User, user_id); grant_entitlement(user, 'ripple_plus', source='admin'); db.session.commit()
    _login(client, user_id)
    text = client.get('/profile/edit').get_data(as_text=True)
    assert 'Profile theme' in text and 'Profile banner' in text
    assert 'Included with Ripple+' not in text
    assert 'See Ripple+ options' not in text


def test_schedule_panel_explains_free_and_ripple_plus_limits(client, app):
    user_id = _user(app, 'schedulerdiscovery'); _login(client, user_id)
    text = client.get('/').get_data(as_text=True)
    assert 'Free accounts can schedule up to 7 days ahead' in text
    assert 'Ripple+ extends this to 90 days' in text


def test_ripple_plus_schedule_panel_has_no_upgrade_pitch(client, app):
    user_id = _user(app, 'plusscheduler')
    with app.app_context():
        user = db.session.get(User, user_id); grant_entitlement(user, 'ripple_plus', source='admin'); db.session.commit()
    _login(client, user_id)
    text = client.get('/').get_data(as_text=True)
    assert 'Ripple+ scheduling: up to 90 days ahead' in text
    assert 'Ripple+ extends this to 90 days' not in text


def test_ripple_plus_analytics_discovers_creator_pro_contextually(client, app):
    user_id = _user(app, 'analyticsdiscovery')
    with app.app_context():
        user = db.session.get(User, user_id); grant_entitlement(user, 'ripple_plus', source='admin'); db.session.commit()
    _login(client, user_id)
    text = client.get('/analytics').get_data(as_text=True)
    assert 'Need professional performance analytics?' in text
    assert 'Compare Creator Pro' in text


def test_creator_pro_subscriber_gets_feature_link_instead_of_sales_pitch(client, app):
    user_id = _user(app, 'prodiscovery')
    with app.app_context():
        user = db.session.get(User, user_id); grant_entitlement(user, 'creator_pro', source='admin'); db.session.commit()
    _login(client, user_id)
    text = client.get('/analytics').get_data(as_text=True)
    assert 'Open Creator Pro' in text
    assert 'Need professional performance analytics?' not in text
