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

**Status:** Completed.

- Provider-neutral transaction and payout state contracts are defined and regression-tested.
- Gross/platform/provider/creator-net fee components must reconcile exactly.
- The initial future support range is USD $1.00–$1,000.00.
- Minimum receipt fields, refund/cancellation, chargeback/dispute, payout, retry/idempotency, reconciliation, privacy, and fail-closed behavior are documented.
- Financial events cannot affect organic ranking, topic/community reputation, verification, moderation authority, or safety exemptions.
- The story performs no checkout, provider API call, transaction persistence, payout, or entitlement grant.
- See `docs/SUPPORT_TRANSACTION_CONTRACT.md` for the normative contract.
- Story 15.2 merged in PR #222.

## Story 15.3 — Supporter memberships and benefits

**Status:** In implementation.

### Current implementation slice

- Adds a dedicated `CreatorMembershipOffering` companion model instead of modifying the mature `User` model.
- Migration `20260907_0035_creator_membership_offering.py` advances from migration `0034`.
- A creator may publish or unpublish one descriptive membership offering with a bounded name and description.
- Creators choose only from Ripple-defined benefit categories: supporter-only creator updates, early access to creator-published material, member Q&A participation, and creator-provided downloadable resources.
- Public membership offerings are visible only when both the creator support profile and the membership offering are enabled.
- Disabling the offering preserves its configuration so the choice is reversible.
- The public page explicitly states that enrollment and payment are not enabled.
- No supporter/member row, payment record, checkout, access-control grant, entitlement, badge, ranking boost, verification benefit, moderation authority, or safety exemption is created.

### Acceptance criteria

- Membership settings require authentication.
- Publishing requires a name, description, and at least one supported benefit.
- Unsupported benefit keys are ignored and cannot become published benefits.
- A public membership page returns 404 unless the creator's support profile and membership offering are both enabled.
- Disabling an offering hides the public page without deleting configuration.
- Creating or publishing an offering grants no entitlement.
- Benefit labels are fixed by Ripple rather than accepting arbitrary promises that the product cannot enforce.
- Tests cover authentication, publication, validation, visibility, reversibility, and the no-entitlement boundary.

### Product boundary

Story 15.3 defines and publishes a future membership offering only. It does **not** enroll supporters, charge money, create recurring billing, activate supporter access, create a membership badge, unlock private content, select a payment provider, or authorize paid/AWS service activation. Those capabilities require later explicit implementation after provider and operational responsibilities are resolved.

## Story 15.4 — Creator/community sustainability analytics

**Status:** Planned.

Add measured support/member analytics only where Ripple has reliable transaction and membership data, with explicit separation from organic-content ranking.

## Story 15.5 — Sustainability integrity and operations review

**Status:** Planned.

Close the sprint with fee/cancellation/payout documentation, abuse and moderation boundaries, privacy/financial-data handling, operational failure modes, and regression evidence.

## Definition of done

Sprint 15 is complete when Ripple has an understandable and reversible creator/community sustainability model with documented payment/fee/cancellation boundaries, measured analytics where justified, and explicit safeguards preventing pay-to-win reach, credibility, or moderation influence.
