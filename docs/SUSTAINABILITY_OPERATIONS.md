# Sustainability Integrity and Operations Review

## Purpose

This review closes Sprint 15 by documenting the operational, financial, privacy, abuse, and product-integrity boundaries that must remain true as Ripple evolves creator/community sustainability features.

The current implementation does **not** move money, enroll supporters, grant paid memberships, create payouts, or activate a payment provider. Creator support and membership pages are publication surfaces; sustainability analytics measure only page visits Ripple actually records.

## Current persisted data

Ripple currently persists only three sustainability-related data classes:

1. **Creator support profile** — whether a creator publishes a support page plus an optional creator-authored support message.
2. **Creator membership offering** — whether a creator publishes a descriptive membership offering, its bounded name/description, and selected Ripple-defined benefit categories.
3. **Sustainability page visit** — deduplicated visitor interest in public support and membership pages.

None of these records represents a financial transaction, supporter enrollment, active membership, entitlement, payout, refund, chargeback, tax record, or provider credential.

## Product-integrity boundary

Payment or supporter status must never purchase or modify:

- organic feed placement or reach;
- topic or community reputation;
- identity-verification approval;
- moderation authority or report priority;
- Community Standards exemptions;
- conversation-health controls;
- reply ordering or contribution-signal weight;
- community roles unless a future community-specific rule is separately designed and reviewed.

Any future feature that proposes one of those couplings requires an explicit product decision rather than being introduced indirectly through payment state.

## Abuse and moderation boundary

Support and membership publication does not immunize a creator or supporter from Community Standards. Moderation actions operate on content/account behavior, not on revenue or payment value.

Financial disputes are not moderation signals. Refunds, chargebacks, failed payments, payout failures, or supporter cancellations must not automatically lower reputation, suppress content, revoke verification, or create moderation penalties.

If a creator account is restricted or content is removed, financial obligations still require separate reconciliation. Moderation must not erase transaction history that would be required for receipts, refunds, disputes, or auditability once money movement exists.

## Fee and cancellation boundary

The normative provider-neutral transaction lifecycle, fee equation, refund/cancellation rules, chargeback behavior, payout states, receipt requirements, and activation gate live in `docs/SUPPORT_TRANSACTION_CONTRACT.md`.

Before checkout is enabled, a provider-specific review must document at minimum:

- displayed platform and provider fees;
- supporter cancellation behavior before settlement;
- partial/full refund mechanics;
- dispute and chargeback processing;
- payout timing, failure, retry, and reversal behavior;
- webhook authenticity and idempotency;
- reconciliation ownership;
- tax/reporting responsibilities;
- provider outage behavior;
- required credentials and secret rotation;
- provider data-retention/deletion constraints.

No provider may be activated merely because the provider-neutral contract exists.

## Privacy and financial-data handling

Current sustainability analytics intentionally avoid payment and enrollment data because those records do not exist.

Future payment persistence may retain only the minimum provider-neutral identifiers and audit fields required for receipts, refunds, disputes, payout reconciliation, and legal/accounting obligations. Ripple must not persist raw card numbers, CVV values, bank credentials, provider API secrets, authentication secrets, or equivalent sensitive payment credentials in application transaction records.

Supporter identity should be stored only when the product actually requires an account relationship or legal/audit requirement. Anonymous/guest support, if ever offered, requires a separate privacy review before implementation.

Financial and membership data must not become inputs to unrelated personalization, inferred ideology, inferred sensitive interests, or advertising profiles.

## Analytics integrity

The current dashboard may report only measured public-page visitor counts over bounded 7/30/90-day windows.

Until real transaction and enrollment records exist, Ripple must not display or infer:

- revenue;
- conversion rate;
- supporter count;
- active-member count;
- churn;
- average revenue per user;
- lifetime value;
- refunds or chargebacks;
- payout totals.

A missing metric should remain visibly unavailable rather than be estimated from page visits.

## Operational failure modes

### Public-page failure

If a support or membership page is disabled or unavailable, it returns its normal unavailable response and records no analytics event. Publication failure must not silently enable a previously disabled page.

### Analytics-write failure

Analytics are non-critical to the public-page response. A future implementation may queue/retry measured events, but it must never block a creator's public page solely because analytics persistence fails. Retries must preserve daily visitor deduplication.

### Provider timeout or ambiguous payment state

Once payments exist, ambiguous provider outcomes fail closed. Ripple must not show success, grant benefits, or schedule payout until provider-confirmed state can be reconciled.

### Duplicate callback or retry

Provider callbacks and operator retries must be idempotent. Repeating an event may confirm existing state but may not duplicate charges, refunds, enrollments, benefits, or payouts.

### Payout failure

A failed payout remains separate from the supporter-facing payment state. Retry/reversal must preserve an auditable history rather than rewriting the original support transaction.

### Database or migration failure

Money-moving features must not be activated unless migration currency and rollback/recovery procedures are proven for the financial schema. A partially applied financial migration is a launch blocker.

### Provider outage

Checkout should become unavailable or fail closed while existing creator pages remain readable where safe. Ripple must not substitute an unverified success state or locally invent a provider result.

## Secrets and deployment boundary

Provider credentials must use the production runtime-secret mechanism; they may not be committed to source control, baked into images, stored in public configuration, or written into transaction rows.

Sprint 8's AWS boundary remains unchanged: repository readiness does not authorize `terraform apply`, AWS resource creation, or recurring infrastructure spend. A future payment provider or paid third-party service also requires explicit activation authorization.

## Reconciliation and operator evidence

Before real money movement, operations must have a documented reconciliation procedure capable of comparing Ripple records with provider records for a bounded period and identifying:

- missing or duplicate transactions;
- fee mismatches;
- refund mismatches;
- disputed/chargeback transactions;
- payout mismatches;
- unresolved provider states.

A release that enables money movement must retain dated evidence of the provider configuration review, webhook verification test, idempotency test, refund test, failure-path test, reconciliation rehearsal, and rollback/disable procedure.

## Regression evidence

Sprint 15 regression coverage establishes that:

- support profiles contain publication state and creator-authored context only;
- membership offerings describe publication state and approved benefit categories only;
- sustainability analytics store measured page-visit data only;
- analytics explicitly report financial/member metrics as unavailable;
- no current sustainability model stores transaction, payout, refund, chargeback, enrollment, entitlement, or provider-secret fields;
- publication and measured analytics do not alter organic reach, reputation, verification, moderation authority, or safety behavior.

## Activation checklist for future money movement

Before enabling checkout or supporter enrollment, all of the following must be true:

- provider selected through an explicit product/operations decision;
- provider-specific contract documented;
- fee disclosure reviewed;
- transaction and payout persistence implemented with migrations and recovery evidence;
- webhook authenticity and idempotency tested;
- cancellation/refund/chargeback behavior tested;
- payout/reversal behavior tested;
- receipts implemented;
- privacy/data-retention review completed;
- tax/reporting ownership documented;
- reconciliation rehearsal completed;
- secrets-management path verified;
- failure/disable/rollback procedure tested;
- no-pay-to-win regression gates passing;
- any required paid service or AWS activation separately authorized.

Until that checklist is satisfied, Ripple's sustainability surfaces remain descriptive and measured-interest features only.