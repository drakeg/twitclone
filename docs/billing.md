# Ripple billing

Ripple uses a provider-neutral `Plan` / `Subscription` / `Entitlement` model and Stripe as the first payment provider.

## Security model

Identity verification and payment are separate. A Stripe payment never sets `User.identity_verified`. The public Verified identity badge is shown only when the account has both:

1. Ripple-approved identity verification, and
2. an active `verified_badge` entitlement.

The browser success URL never grants the entitlement. Subscription access is synchronized only from Stripe webhook events whose signature validates against `STRIPE_WEBHOOK_SECRET`.

## Local/test-mode setup

Leave Stripe disabled unless you are intentionally testing billing:

```text
STRIPE_BILLING_ENABLED=false
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

To test with Stripe test mode, use a Stripe test secret key and a webhook secret, then enable billing:

```text
STRIPE_BILLING_ENABLED=true
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Restart/rebuild Ripple after changing dependency or environment configuration.

Seed/update the provider-neutral catalog with:

```bash
docker compose exec web flask --app application seed-billing-plans
```

For local webhook forwarding with the Stripe CLI, forward events to the externally exposed Ripple port, for example:

```bash
stripe listen --forward-to localhost:8001/billing/webhook
```

Use the `whsec_...` secret printed by the Stripe CLI as `STRIPE_WEBHOOK_SECRET` for that local listener.

## Webhook events

Ripple currently consumes:

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

The synchronization is idempotent by Stripe subscription ID. Active subscriptions grant the plan entitlement only while the Ripple identity remains approved. Past-due, canceled, expired, or otherwise inactive subscriptions revoke the entitlement.

## Customer portal

Once a Stripe customer ID is associated with a local subscription, the Billing page can open Stripe's hosted customer portal so users can manage payment methods and cancellation without Ripple storing card data.

## Initial verified-badge catalog

- Individual: $2.99/month or $29.99/year
- Organization: $7.99/month or $79.99/year

Pricing is application-owned plan metadata. Stripe Checkout receives the selected plan's amount and recurring interval from Ripple.
