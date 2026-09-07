# Sprint 15 — Creator and Community Sustainability

**Status:** In implementation.

## Goal

Expand sustainable creator/community value without selling credibility, moderation influence, or organic reach.

## Product principles

- Core conversation, safety, community participation, and reputation remain available without payment.
- Payment must never purchase organic ranking, moderation authority, verification approval, or topic/community reputation.
- New money-moving capability must document fees, provider responsibilities, cancellation/refund behavior, payouts, and failure handling before activation.
- Creator/community support must be explicitly opted into and reversible.
- Analytics claims remain limited to data Ripple actually measures.
- Existing AWS/no-spend restrictions remain unchanged.

## Story 15.1 — Creator support foundation

**Status:** Completed.

- Dedicated `CreatorSupportProfile` persistence keeps creator-support state isolated from the mature `User` model.
- Creators can explicitly publish/unpublish a bounded support message and receive a stable public support page only while enabled.
- Disabled/unconfigured support pages remain private, and disabling preserves reversible configuration.
- No checkout, payment, entitlement, ranking, reputation, verification, or moderation effect is created.
- Migration `20260906_0034_creator_support_profile.py` advances from migration `0033`.
- Story 15.1 merged in PR #221.

## Story 15.2 — Support transaction contract

**Status:** In implementation.

### Current implementation slice

- Adds provider-neutral transaction states: `created`, `pending`, `succeeded`, `failed`, `canceled`, `partially_refunded`, `refunded`, and `chargeback`.
- Defines narrow allowed state transitions so failed/canceled transactions cannot later be rewritten as successful history.
- Defines independent payout states: `not_ready`, `pending`, `paid`, `failed`, and `reversed`.
- Adds a validated fee contract requiring gross amount to reconcile exactly to platform fee + provider fee + creator net.
- Establishes an initial USD support range of $1.00 through $1,000.00 for the future payment implementation.
- Defines the minimum supporter receipt fields Ripple must be able to present after settlement.
- Documents cancellation, partial/full refund, chargeback/dispute, payout, provider retry/idempotency, reconciliation, privacy, and failure-state rules.
- Financial events are explicitly prohibited from affecting organic feed ranking, topic/community reputation, verification, moderation authority, or safety exemptions.
- Unknown/contradictory provider state must fail closed for reconciliation rather than assuming payment success.
- This story performs no checkout, provider API call, transaction persistence, payout, or entitlement grant.

### Acceptance criteria

- Fee components cannot be negative and must reconcile exactly to gross amount.
- Unsupported currencies and out-of-range support amounts are rejected by the contract.
- Transaction and payout transitions are explicit and regression-tested.
- Receipt validation requires a transaction reference, creator reference, status, currency, and reconciled fee data.
- Successful transactions cannot be rewritten as pending/created; failed/canceled transactions cannot later become successful.
- Chargebacks remain financial/provider events rather than moderation or reputation signals.
- The contract prohibits storage of raw card/bank credentials, CVV, provider secrets, or authentication secrets in transaction records.
- Provider selection and actual money movement remain separately gated.

### Product boundary

Story 15.2 defines behavior only. It does **not** activate Stripe or any other provider, create checkout/webhook routes, move money, create payouts, grant memberships, add transaction persistence, or authorize AWS/paid-service spend. Provider-specific implementation remains a later explicit story/decision after fee, webhook, refund, dispute, tax, payout, reconciliation, and secret-handling responsibilities are resolved.

See `docs/SUPPORT_TRANSACTION_CONTRACT.md` for the normative contract.

## Story 15.3 — Supporter memberships and benefits

**Status:** Planned.

Evaluate optional creator/community membership benefits that provide convenience or access without buying ranking, reputation, moderation authority, verification, or safety exemptions.

## Story 15.4 — Creator/community sustainability analytics

**Status:** Planned.

Add measured support/member analytics only where Ripple has reliable transaction and membership data, with explicit separation from organic-content ranking.

## Story 15.5 — Sustainability integrity and operations review

**Status:** Planned.

Close the sprint with fee/cancellation/payout documentation, abuse and moderation boundaries, privacy/financial-data handling, operational failure modes, and regression evidence.

## Definition of done

Sprint 15 is complete when Ripple has an understandable and reversible creator/community sustainability model with documented payment/fee/cancellation boundaries, measured analytics where justified, and explicit safeguards preventing pay-to-win reach, credibility, or moderation influence.
