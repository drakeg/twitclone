"""Provider-neutral billing catalog and entitlement helpers."""

from twitclone.extensions import db
from twitclone.models import Entitlement, Plan

VERIFIED_INDIVIDUAL_MONTHLY = {
    'key': 'verified_individual_monthly',
    'name': 'Verified Individual',
    'description': 'Maintain the Verified identity badge after identity approval.',
    'amount_cents': 299,
    'currency': 'USD',
    'interval': 'month',
    'entitlement_key': 'verified_badge',
}
VERIFIED_INDIVIDUAL_YEARLY = {
    'key': 'verified_individual_yearly',
    'name': 'Verified Individual',
    'description': 'Maintain the Verified identity badge after identity approval.',
    'amount_cents': 2999,
    'currency': 'USD',
    'interval': 'year',
    'entitlement_key': 'verified_badge',
}
VERIFIED_ORGANIZATION_MONTHLY = {
    'key': 'verified_organization_monthly',
    'name': 'Verified Organization',
    'description': 'Maintain the Verified organization badge after identity approval.',
    'amount_cents': 799,
    'currency': 'USD',
    'interval': 'month',
    'entitlement_key': 'verified_badge',
}
VERIFIED_ORGANIZATION_YEARLY = {
    'key': 'verified_organization_yearly',
    'name': 'Verified Organization',
    'description': 'Maintain the Verified organization badge after identity approval.',
    'amount_cents': 7999,
    'currency': 'USD',
    'interval': 'year',
    'entitlement_key': 'verified_badge',
}
RIPPLE_PLUS_MONTHLY = {
    'key': 'ripple_plus_monthly',
    'name': 'Ripple+',
    'description': 'Premium posting, extended scheduling, and personal analytics.',
    'amount_cents': 499,
    'currency': 'USD',
    'interval': 'month',
    'entitlement_key': 'ripple_plus',
}
RIPPLE_PLUS_YEARLY = {
    'key': 'ripple_plus_yearly',
    'name': 'Ripple+',
    'description': 'Premium posting, extended scheduling, and personal analytics.',
    'amount_cents': 4999,
    'currency': 'USD',
    'interval': 'year',
    'entitlement_key': 'ripple_plus',
}

DEFAULT_PLANS = (
    VERIFIED_INDIVIDUAL_MONTHLY,
    VERIFIED_INDIVIDUAL_YEARLY,
    VERIFIED_ORGANIZATION_MONTHLY,
    VERIFIED_ORGANIZATION_YEARLY,
    RIPPLE_PLUS_MONTHLY,
    RIPPLE_PLUS_YEARLY,
)


def ensure_default_plans():
    """Create/update Ripple-owned plan metadata without contacting a payment provider."""
    for spec in DEFAULT_PLANS:
        plan = Plan.query.filter_by(key=spec['key']).first()
        if plan is None:
            plan = Plan(key=spec['key'])
            db.session.add(plan)
        for field, value in spec.items():
            setattr(plan, field, value)
    db.session.commit()


def grant_entitlement(user, key, *, source='admin', subscription=None, expires_at=None):
    entitlement = Entitlement.query.filter_by(user_id=user.id, key=key).first()
    if entitlement is None:
        entitlement = Entitlement(user_id=user.id, key=key)
        db.session.add(entitlement)
    entitlement.active = True
    entitlement.source = source
    entitlement.subscription = subscription
    entitlement.expires_at = expires_at
    return entitlement


def revoke_entitlement(user, key):
    entitlement = Entitlement.query.filter_by(user_id=user.id, key=key).first()
    if entitlement is not None:
        entitlement.active = False
    return entitlement
