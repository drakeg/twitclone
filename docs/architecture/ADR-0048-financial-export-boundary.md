# ADR-0048: Financial portability without payment-secret exposure

## Status

Accepted.

## Context

Ripple persists local subscription and entitlement state for an account. It does not persist card or bank credentials, invoices, charge receipts, or creator-support transactions. Provider customer and subscription identifiers are operational correlation keys, not portable payment credentials, and exposing them adds risk without making the export more understandable.

Plan prices are mutable catalog data. A current plan amount cannot be represented as proof of a historical charge.

## Decision

- Advance `ripple-portable-export` to version 3 for subscription and entitlement state.
- Include only subscriptions and entitlements owned by the requester.
- Include plan key/name, current catalog amount in minor units, currency, interval, provider name, status, current service period, and local timestamps.
- Name the plan amount `catalog_amount_cents`; do not describe it as paid, charged, invoiced, or receipted.
- Exclude provider customer/subscription identifiers, payment credentials, invoices, charge receipts, webhook payloads, and secrets.
- State that creator-support transaction history is unavailable because Ripple does not process or persist those transactions.
- Keep export access free and independent of entitlement status.

## Consequences

- Users can understand their current Ripple subscription and feature-access state.
- The export does not become a source of operational provider identifiers or payment secrets.
- The document is not a tax record, invoice archive, bank statement, or proof of payment.
- Future receipt or support-transaction export requires real persisted records and a separately reviewed retention/privacy contract.
