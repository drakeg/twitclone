"""Regression coverage for provider-neutral monetization foundations."""

from twitclone.billing import ensure_default_plans, grant_entitlement, revoke_entitlement
from twitclone.extensions import db
from twitclone.models import Entitlement, Plan, User


def _user(app, username='paiduser'):
    with app.app_context():
        user = User(username=username, email=f'{username}@example.com', password='hash')
        db.session.add(user)
        db.session.commit()
        return user.id


def test_default_plans_are_idempotent(app):
    with app.app_context():
        ensure_default_plans()
        ensure_default_plans()
        assert Plan.query.count() == 6
        monthly = Plan.query.filter_by(key='verified_individual_monthly').one()
        yearly = Plan.query.filter_by(key='verified_individual_yearly').one()
        org = Plan.query.filter_by(key='verified_organization_monthly').one()
        plus_monthly = Plan.query.filter_by(key='ripple_plus_monthly').one()
        plus_yearly = Plan.query.filter_by(key='ripple_plus_yearly').one()
        assert monthly.amount_cents == 299
        assert yearly.amount_cents == 2999
        assert org.amount_cents == 799
        assert monthly.entitlement_key == 'verified_badge'
        assert plus_monthly.amount_cents == 499
        assert plus_yearly.amount_cents == 4999
        assert plus_monthly.entitlement_key == 'ripple_plus'


def test_identity_approval_does_not_automatically_activate_paid_badge(app):
    user_id = _user(app)
    with app.app_context():
        user = db.session.get(User, user_id)
        user.identity_verified = True
        db.session.commit()
        assert user.verified_badge_active is False


def test_verified_badge_requires_identity_and_active_entitlement(app):
    user_id = _user(app, 'badgeuser')
    with app.app_context():
        user = db.session.get(User, user_id)
        grant_entitlement(user, 'verified_badge', source='admin')
        db.session.commit()
        assert user.verified_badge_active is False
        user.identity_verified = True
        db.session.commit()
        assert user.verified_badge_active is True
        revoke_entitlement(user, 'verified_badge')
        db.session.commit()
        assert Entitlement.query.filter_by(user_id=user.id, key='verified_badge').one().active is False
        assert user.verified_badge_active is False


def test_seed_billing_plans_cli_is_safe_to_repeat(app):
    runner = app.test_cli_runner()
    first = runner.invoke(args=['seed-billing-plans'])
    second = runner.invoke(args=['seed-billing-plans'])
    assert first.exit_code == 0
    assert second.exit_code == 0
    with app.app_context():
        assert Plan.query.count() == 6
