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

**Status:** In implementation.

### Current implementation slice

- Adds a dedicated `CreatorSupportProfile` record rather than modifying the mature `User` model.
- Creators can explicitly publish or unpublish an informational support page.
- A support message is required before the public page can be enabled and is bounded to 280 characters.
- Public support pages are available only while the creator has explicitly enabled them.
- Disabling support hides the public page without deleting the creator's stored support profile.
- The UI states prominently that no payment is processed in this story.
- Enabling support grants no entitlement and changes no feed ranking, reputation, verification, or moderation behavior.
- Migration `20260906_0034_creator_support_profile.py` advances from migration `0033`.

### Acceptance criteria

- Support settings require authentication.
- Enabling support requires a non-empty creator-authored message.
- Enabled support profiles have a stable public URL.
- Disabled/unconfigured support profiles are not publicly readable.
- Support enablement creates no paid entitlement and triggers no checkout/provider action.
- Creator support state is reversible without deleting the record.
- Tests cover authentication, publication, validation, disable/re-enable lifecycle, bounded text, and the no-entitlement boundary.

### Product boundary

Story 15.1 does **not** process money. Payment provider selection, fees, checkout, receipts, refunds/cancellation, chargebacks, payouts, tax handling, supporter memberships, paid benefits, and creator/community revenue analytics remain future stories.

## Story 15.2 — Support transaction contract

**Status:** Planned.

Define the provider-neutral transaction, fee, receipt, refund/cancellation, chargeback, payout, and failure-state contract before enabling support payments.

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
