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

**Status:** Completed.

- Adds a dedicated `CreatorMembershipOffering` companion model instead of modifying the mature `User` model.
- Migration `20260907_0035_creator_membership_offering.py` advances from migration `0034`.
- A creator may publish or unpublish one descriptive membership offering with a bounded name and description.
- Creators choose only from Ripple-defined benefit categories: supporter-only creator updates, early access to creator-published material, member Q&A participation, and creator-provided downloadable resources.
- Public membership offerings are visible only when both the creator support profile and the membership offering are enabled.
- Disabling the offering preserves its configuration so publication is reversible.
- The public page explicitly states that enrollment and payment are not enabled.
- No supporter/member row, payment record, checkout, access-control grant, entitlement, badge, ranking boost, verification benefit, moderation authority, or safety exemption is created.
- Story 15.3 merged in PR #223.

## Story 15.4 — Creator/community sustainability analytics

**Status:** In implementation.

### Current implementation slice

- Adds `SustainabilityPageVisit`, a dedicated measured-event model for public creator-support and membership-offering page visits.
- Migration `20260907_0036_sustainability_page_visits.py` advances from migration `0035`.
- Public page interest is deduplicated to one visitor per creator/page/day.
- Authenticated creator self-views are excluded.
- Only successful public support/membership pages record visits; disabled or unavailable pages do not create analytics events.
- `/creator/support/analytics` provides 7/30/90-day measured summaries for support-page and membership-page visitors.
- Daily measured-interest rows are shown transparently without an engagement score or conversion inference.
- Revenue, payment conversion, supporter count, active member count, churn, refunds, payouts, and lifetime value remain explicitly unavailable because Ripple does not yet have the underlying transaction or enrollment records.
- Analytics do not affect organic ranking, reputation, verification, moderation authority, or safety behavior.

### Acceptance criteria

- Sustainability analytics require authentication.
- Repeated views by the same visitor on the same public page/day count once.
- Support and membership pages are measured separately.
- A creator's own authenticated views are not counted.
- 404/disabled pages create no analytics event.
- The dashboard supports bounded 7/30/90-day views and reports only measured visitor data.
- The UI explicitly explains why revenue/supporter/member metrics are absent instead of displaying inferred or placeholder values.
- Tests cover authentication, deduplication, self-view exclusion, page-type separation, disabled-page behavior, and the no-invented-metrics boundary.

### Product boundary

Story 15.4 does not add checkout, transaction persistence, recurring billing, membership enrollment, payouts, conversion attribution, or financial analytics. It measures only real visits to public sustainability surfaces that Ripple already serves. Financial/member analytics require future real transaction or membership records.

## Story 15.5 — Sustainability integrity and operations review

**Status:** Planned.

Close the sprint with fee/cancellation/payout documentation, abuse and moderation boundaries, privacy/financial-data handling, operational failure modes, and regression evidence.

## Definition of done

Sprint 15 is complete when Ripple has an understandable and reversible creator/community sustainability model with documented payment/fee/cancellation boundaries, measured analytics where justified, and explicit safeguards preventing pay-to-win reach, credibility, or moderation influence.
