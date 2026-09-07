# Creator Support Transaction Contract

## Purpose

This contract defines how Ripple must represent creator-support payments before any provider-backed checkout is enabled. It is intentionally provider-neutral and does not authorize activation of a payment provider, AWS resource, recurring service, or money movement.

## Transaction lifecycle

Supported transaction states are `created`, `pending`, `succeeded`, `failed`, `canceled`, `partially_refunded`, `refunded`, and `chargeback`.

Allowed transitions are intentionally narrow:

- `created` -> `pending`, `canceled`, or `failed`
- `pending` -> `succeeded`, `canceled`, or `failed`
- `succeeded` -> `partially_refunded`, `refunded`, or `chargeback`
- `partially_refunded` -> `partially_refunded`, `refunded`, or `chargeback`
- `refunded` -> `chargeback`
- `failed`, `canceled`, and `chargeback` are terminal for the original transaction

Provider callbacks must be idempotent. A repeated event may confirm the current state, but it must not create a second support transaction or duplicate a refund/payout.

## Amount and fee contract

The first supported currency is USD. The contract accepts support amounts from $1.00 through $1,000.00.

Every settled transaction must expose an auditable fee breakdown:

`gross amount = platform fee + provider fee + creator net`

No fee may be negative. Ripple must disclose the platform fee before checkout once payments are implemented. Provider fees must be recorded from provider-confirmed data rather than guessed. The creator net amount must remain derivable from the stored fee breakdown.

## Receipt contract

A completed support receipt must be able to show at least:

- Ripple transaction reference
- creator identity/reference
- gross amount and currency
- Ripple/platform fee
- provider processing fee
- creator net amount
- current transaction status
- transaction timestamp once persistence is implemented

A receipt must never expose raw payment-card, bank-account, authentication, or provider-secret data.

## Refund and cancellation rules

Cancellation applies only before successful settlement. Once a transaction succeeds, later reversal is represented as a refund, partial refund, or chargeback rather than rewriting history.

Future refund implementation must record the refunded amount, actor/source, provider reference, timestamp, and reason/category. Multiple partial refunds must never exceed the original settled gross amount. A full refund is terminal except for a later provider-reported chargeback state.

## Chargebacks and disputes

Chargebacks are provider-originated financial events and must not be treated as moderation violations or reputation signals. A chargeback must not automatically penalize a creator's feed ranking, topic/community reputation, verification, or moderation authority.

Future dispute handling must preserve the original transaction and append provider dispute references/status rather than deleting financial history.

## Payout lifecycle

Payout states are `not_ready`, `pending`, `paid`, `failed`, and `reversed`.

Allowed transitions are:

- `not_ready` -> `pending`
- `pending` -> `paid` or `failed`
- `failed` -> `pending`
- `paid` -> `reversed`

Payout state is separate from supporter-facing transaction state. A supporter payment may succeed before creator payout completes.

## Failure handling

Provider timeouts, webhook retries, payout failures, and temporary network errors must be recoverable without duplicating money movement. Failed provider operations must retain enough provider-neutral identifiers for reconciliation while avoiding storage of sensitive payment credentials.

Unknown or contradictory provider states must fail closed: Ripple should hold the transaction for reconciliation rather than granting benefits, payouts, or success messaging based on an assumption.

## Privacy and security boundary

Ripple may store provider-neutral transaction IDs, provider object references, amounts, fee components, timestamps, status, creator/supporter account references when applicable, and audit metadata. Ripple must not store raw PAN/card numbers, CVV, bank credentials, provider API secrets, or authentication secrets in transaction records.

Payment data must not become an input to organic feed ranking, topic/community reputation, verification, moderation authority, or safety exemptions.

## Activation gate

This contract does **not** activate payment processing. Before money movement is enabled, a later story/decision must select a provider and document provider-specific fees, checkout behavior, webhook verification/idempotency, receipts, refunds, chargebacks, payouts, tax responsibilities, operational reconciliation, and required secrets/configuration. Any paid service or AWS activation remains separately authorized.
