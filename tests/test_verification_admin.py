"""Regression coverage for Ripple verification and administration."""

from twitclone.extensions import db
from twitclone.models import User, VerificationRequest


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _user(app, username='alice', email='alice@example.com', **kwargs):
    with app.app_context():
        user = User(username=username, email=email, password='hash', **kwargs)
        db.session.add(user)
        db.session.commit()
        return user.id


def test_regular_user_cannot_access_admin_dashboard(client, app):
    user_id = _user(app)
    _login(client, user_id)
    assert client.get('/admin').status_code == 403


def test_super_admin_can_access_admin_dashboard(client, app):
    user_id = _user(app, is_admin=True, is_super_admin=True)
    _login(client, user_id)
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Ripple Admin' in response.data


def test_user_can_submit_verification_request(client, app):
    user_id = _user(app)
    _login(client, user_id)
    response = client.post(
        '/verification/apply',
        data={
            'verification_type': 'person',
            'display_name': 'Alice Example',
            'official_website': 'https://example.com',
            'supporting_information': 'Official website links back to this Ripple account.',
        },
    )
    assert response.status_code == 302
    with app.app_context():
        request = VerificationRequest.query.filter_by(user_id=user_id).one()
        assert request.status == 'pending'
        assert request.verification_type == 'person'


def test_admin_approval_sets_verified_identity(client, app):
    applicant_id = _user(app, username='alice', email='alice@example.com')
    admin_id = _user(
        app,
        username='owner',
        email='owner@example.com',
        is_admin=True,
        is_super_admin=True,
    )
    with app.app_context():
        verification = VerificationRequest(
            user_id=applicant_id,
            verification_type='person',
            display_name='Alice Example',
            supporting_information='Public evidence',
        )
        db.session.add(verification)
        db.session.commit()
        request_id = verification.id

    _login(client, admin_id)
    response = client.post(
        f'/admin/verification/{request_id}',
        data={'action': 'approve', 'review_notes': 'Identity confirmed.'},
    )
    assert response.status_code == 302
    with app.app_context():
        applicant = db.session.get(User, applicant_id)
        verification = db.session.get(VerificationRequest, request_id)
        assert applicant.identity_verified is True
        assert applicant.verification_type == 'person'
        assert verification.status == 'approved'
        assert verification.reviewed_by_id == admin_id


def test_make_super_admin_cli_promotes_existing_user(app):
    user_id = _user(app)
    runner = app.test_cli_runner()
    result = runner.invoke(args=['make-super-admin', 'alice@example.com'])
    assert result.exit_code == 0
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.is_admin is True
        assert user.is_super_admin is True
