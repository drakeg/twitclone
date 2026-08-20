"""Regression coverage for Ripple+ profile customization."""

from io import BytesIO

from PIL import Image

from twitclone.billing import grant_entitlement
from twitclone.extensions import db
from twitclone.models import User


def _user(app, username='alice', *, ripple_plus=False):
    with app.app_context():
        user = User(username=username, email=f'{username}@example.com', password='hash')
        db.session.add(user)
        db.session.flush()
        if ripple_plus:
            grant_entitlement(user, 'ripple_plus', source='admin')
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _png_upload():
    payload = BytesIO()
    Image.new('RGB', (32, 16), 'white').save(payload, format='PNG')
    payload.seek(0)
    return payload


def test_free_user_sees_ripple_plus_customization_upsell(client, app):
    user_id = _user(app)
    _login(client, user_id)
    response = client.get('/profile/edit')
    assert response.status_code == 200
    assert b'Ripple+ profile customization' in response.data
    assert b'View Ripple+ plans' in response.data
    assert b'name="profile_theme"' not in response.data


def test_free_user_cannot_change_premium_theme_by_posting_fields(client, app):
    user_id = _user(app)
    _login(client, user_id)
    response = client.post('/profile/edit', data={
        'username': 'alice',
        'email': 'alice@example.com',
        'bio': 'Free profile',
        'profile_theme': 'sunset',
    })
    assert response.status_code == 302
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.profile_theme == 'ripple'
        assert user.profile_banner is None


def test_ripple_plus_user_can_set_theme_and_banner(client, app):
    user_id = _user(app, ripple_plus=True)
    _login(client, user_id)
    response = client.post(
        '/profile/edit',
        data={
            'username': 'alice',
            'email': 'alice@example.com',
            'bio': 'Premium profile',
            'profile_theme': 'sunset',
            'profile_banner': (_png_upload(), 'banner.png'),
        },
        content_type='multipart/form-data',
    )
    assert response.status_code == 302
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.profile_theme == 'sunset'
        assert user.profile_banner.startswith('banner_')
        assert user.profile_banner.endswith('.png')
        banner_name = user.profile_banner

    response = client.get('/profile/alice')
    assert response.status_code == 200
    assert banner_name.encode() in response.data
    assert b'Ripple+' in response.data


def test_invalid_banner_is_rejected_without_replacing_existing_banner(client, app):
    user_id = _user(app, ripple_plus=True)
    with app.app_context():
        user = db.session.get(User, user_id)
        user.profile_banner = 'banner_existing.png'
        db.session.commit()
    _login(client, user_id)
    response = client.post(
        '/profile/edit',
        data={
            'username': 'alice',
            'email': 'alice@example.com',
            'bio': '',
            'profile_theme': 'forest',
            'profile_banner': (BytesIO(b'not an image'), 'fake.png'),
        },
        content_type='multipart/form-data',
    )
    assert response.status_code == 200
    assert b'not a valid image' in response.data
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.profile_banner == 'banner_existing.png'


def test_lapsed_ripple_plus_profile_falls_back_to_default_public_appearance(client, app):
    user_id = _user(app, ripple_plus=True)
    with app.app_context():
        user = db.session.get(User, user_id)
        user.profile_theme = 'violet'
        user.profile_banner = 'banner_saved.png'
        entitlement = next(item for item in user.entitlements if item.key == 'ripple_plus')
        entitlement.active = False
        db.session.commit()
    _login(client, user_id)
    response = client.get('/profile/alice')
    assert response.status_code == 200
    assert b'banner_saved.png' not in response.data
    assert b'background: linear-gradient(135deg, #2563eb, #06b6d4);' in response.data


def test_ripple_plus_user_can_remove_banner(client, app):
    user_id = _user(app, ripple_plus=True)
    with app.app_context():
        user = db.session.get(User, user_id)
        user.profile_banner = 'banner_saved.png'
        db.session.commit()
    _login(client, user_id)
    response = client.post('/profile/edit', data={
        'username': 'alice',
        'email': 'alice@example.com',
        'bio': '',
        'profile_theme': 'slate',
        'remove_banner': '1',
    })
    assert response.status_code == 302
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.profile_banner is None
        assert user.profile_theme == 'slate'
