"""Stripe Checkout, portal, and webhook-driven subscription lifecycle."""

from datetime import UTC, datetime

import stripe
from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.billing import ensure_default_plans, grant_entitlement, revoke_entitlement
from twitclone.extensions import csrf, db
from twitclone.models import Plan, Subscription, User
from twitclone.payments import payments_blueprint


def _stripe_ready(): return bool(current_app.config.get('STRIPE_BILLING_ENABLED') and current_app.config.get('STRIPE_SECRET_KEY'))
def _configure_stripe(): stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
def _dt(value): return datetime.fromtimestamp(value, tz=UTC).replace(tzinfo=None) if value else None


def _eligible_plan(plan):
    if plan.entitlement_key in {'ripple_plus', 'creator_pro'}: return True
    if plan.entitlement_key != 'verified_badge' or not current_user.identity_verified: return False
    if current_user.verification_type == 'organization': return plan.key.startswith('verified_organization_')
    return plan.key.startswith('verified_individual_')


def _sync_subscription_object(obj):
    metadata = obj.get('metadata') or {}; user_id = metadata.get('ripple_user_id'); plan_key = metadata.get('ripple_plan_key')
    if not user_id or not plan_key: return
    user = db.session.get(User, int(user_id)); plan = Plan.query.filter_by(key=plan_key).first()
    if user is None or plan is None: return
    provider_id = obj.get('id'); subscription = Subscription.query.filter_by(provider_subscription_id=provider_id).first()
    if subscription is None:
        subscription = Subscription(user_id=user.id, plan_id=plan.id, provider='stripe', provider_subscription_id=provider_id); db.session.add(subscription)
    status = obj.get('status') or 'pending'
    subscription.status = 'active' if status in {'active','trialing'} else ('past_due' if status in {'past_due','unpaid'} else ('canceled' if status in {'canceled','incomplete_expired'} else 'pending'))
    subscription.provider_customer_id = obj.get('customer'); subscription.current_period_start = _dt(obj.get('current_period_start')); subscription.current_period_end = _dt(obj.get('current_period_end'))
    entitlement_allowed = plan.entitlement_key != 'verified_badge' or user.identity_verified
    if subscription.status == 'active' and entitlement_allowed: grant_entitlement(user, plan.entitlement_key, source='stripe', subscription=subscription, expires_at=subscription.current_period_end)
    else: revoke_entitlement(user, plan.entitlement_key)
    db.session.commit()


@payments_blueprint.route('/billing')
@login_required
def billing_home():
    ensure_default_plans(); plans = Plan.query.filter_by(active=True).order_by(Plan.amount_cents.asc()).all(); eligible_plans = [plan for plan in plans if _eligible_plan(plan)]
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    return render_template('billing.html', plans=eligible_plans, subscriptions=subscriptions, stripe_enabled=_stripe_ready())


@payments_blueprint.route('/billing/checkout/<plan_key>', methods=['POST'])
@login_required
def checkout(plan_key):
    ensure_default_plans(); plan = Plan.query.filter_by(key=plan_key, active=True).first_or_404()
    if not _eligible_plan(plan):
        if plan.entitlement_key == 'verified_badge' and not current_user.identity_verified:
            flash('Ripple must approve your identity before you can activate a verified badge.', 'warning'); return redirect(url_for('admin.apply_verification'))
        abort(403)
    if not _stripe_ready(): flash('Paid subscriptions are not configured yet.', 'warning'); return redirect(url_for('payments.billing_home'))
    existing = Subscription.query.join(Plan).filter(Subscription.user_id == current_user.id, Subscription.status == 'active', Plan.entitlement_key == plan.entitlement_key).first()
    if existing: flash(f'You already have an active {plan.name} subscription. Use Manage billing instead.', 'info'); return redirect(url_for('payments.billing_home'))
    _configure_stripe()
    session = stripe.checkout.Session.create(mode='subscription', customer_email=current_user.email, line_items=[{'price_data':{'currency':plan.currency.lower(),'unit_amount':plan.amount_cents,'recurring':{'interval':plan.interval},'product_data':{'name':f'Ripple {plan.name}','description':plan.description or ''}},'quantity':1}], subscription_data={'metadata':{'ripple_user_id':str(current_user.id),'ripple_plan_key':plan.key}}, metadata={'ripple_user_id':str(current_user.id),'ripple_plan_key':plan.key}, success_url=url_for('payments.checkout_success', _external=True)+'?session_id={CHECKOUT_SESSION_ID}', cancel_url=url_for('payments.billing_home', _external=True))
    return redirect(session.url, code=303)


@payments_blueprint.route('/billing/success')
@login_required
def checkout_success(): flash('Payment was submitted. Paid features activate after Ripple receives Stripe confirmation.', 'success'); return redirect(url_for('payments.billing_home'))


@payments_blueprint.route('/billing/portal', methods=['POST'])
@login_required
def customer_portal():
    if not _stripe_ready(): flash('Billing management is not configured yet.', 'warning'); return redirect(url_for('payments.billing_home'))
    subscription = Subscription.query.filter_by(user_id=current_user.id).filter(Subscription.provider_customer_id.isnot(None)).order_by(Subscription.created_at.desc()).first()
    if subscription is None: flash('No Stripe billing account is associated with your Ripple account yet.', 'warning'); return redirect(url_for('payments.billing_home'))
    _configure_stripe(); session = stripe.billing_portal.Session.create(customer=subscription.provider_customer_id, return_url=url_for('payments.billing_home', _external=True)); return redirect(session.url, code=303)


@payments_blueprint.route('/billing/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    if not secret: abort(503)
    try: event = stripe.Webhook.construct_event(request.get_data(), request.headers.get('Stripe-Signature',''), secret)
    except (ValueError, stripe.error.SignatureVerificationError): abort(400)
    if event['type'] in {'customer.subscription.created','customer.subscription.updated','customer.subscription.deleted'}: _sync_subscription_object(event['data']['object'])
    return '', 200
