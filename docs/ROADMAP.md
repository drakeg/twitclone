# Product Roadmap

This roadmap is intentionally incremental. Sprint scope may be refined as the repository is tested, but a sprint's goal and acceptance criteria should remain stable once implementation begins.

## Sprint 0 — Project foundation and assessment

**Goal:** Establish the project baseline, working agreements, architecture record, and prioritized backlog.

**Status:** Completed.

## Sprint 1 — Secure, reproducible development baseline

**Goal:** Make the existing application safe and predictable to install and run locally.

**Status:** Completed. Environment-backed configuration, dependency reconciliation, reproducible database migrations, smoke coverage, and CI are now established. The original Sprint 1 tracker issues are historical completion records rather than active backlog.

## Sprint 2 — Application structure and test foundation

**Goal:** Reduce risk by separating concerns without changing user-visible behavior.

**Status:** Completed. The application factory, separated configuration/extensions/models/routes, controlled scheduler startup, and authentication/timeline test foundations are in place.

## Sprint 3 — Core timeline and post reliability

**Goal:** Make the primary posting and timeline workflows consistent and well-tested.

**Status:** Completed. Post validation, authorization, timeline normalization/order/visibility, and pagination are covered by the current regression suite.

## Sprint 4 — Social interactions and notifications

**Goal:** Harden follows, bookmarks, messaging, and notifications.

**Status:** Completed and extended. Duplicate relationships are prevented, messaging and notification lifecycles are tested, deletion/read behavior is supported, mentions and followed hashtags are integrated, and notifications link to actionable context.

## Sprint 5 — Media, polls, and scheduling

**Goal:** Secure and stabilize advanced content capabilities.

**Status:** Completed. Media validation, poll integrity/expiration, and out-of-process scheduled publishing are established and tested.

## Product expansion — community, identity, and sustainable monetization

After the reliability baseline, Ripple expanded deliberately without removing useful free participation.

**Delivered capabilities include:**

- Community standards, reporting, moderation review, and reporter/poster resolution notifications
- Administrative identity-verification workflow and paid Verified identity badge activation
- Ripple+ convenience/customization subscription
- Creator Pro measured analytics, historical tracking, and evidence-based performance insights
- Plans & Pricing storefront and Membership/account-status management
- Restrained contextual premium-feature discovery
- Demo/sample content for first-time visitors

## Sprint 6 — Deployment and operations readiness

**Goal:** Prepare a documented, low-cost deployment path.

**Status:** Completed through the application/operations readiness boundary.

Story 6.4 documents the durable-state boundary, recovery objectives, backup and restore rehearsal, rollback decision tree, and a dated low-traffic deployment estimate. Story 6.5 implements the selected private S3-compatible adapter while preserving local filesystem-backed Compose. Story 6.6 adds a dry-run-first, repeatable, content-verified command for migrating existing filesystem media to the configured private bucket. Story 6.7 adds a production-only deployment preflight that proves database connectivity, migration currency, and private media read/write/delete access before traffic is enabled. Story 6.8 supplies standard release-readiness and restore-rehearsal evidence records so every launch gate has an owner, timestamp, result, and reviewable disposition.

Actual AWS infrastructure provisioning remains separate future work. Issue #16 is the current infrastructure tracker and must be re-evaluated against the present application architecture and current AWS pricing before implementation.

## Priority design sprint — UI cleanup and visual refresh

**Goal:** Make Ripple feel polished, welcoming, and easy to navigate.

**Status:** Completed. A shared visual system, responsive navigation, refreshed primary flows, and regression coverage are in place.

## Sprint 7 — Accessible interaction and content

**Goal:** Make Ripple's core flows understandable and operable with keyboards, assistive technology, zoom, and reduced-motion preferences.

**Status:** Automated/remediable implementation completed through Story 7.4. Manual assistive-technology evidence remains an explicit release gate; Ripple does not claim WCAG conformance from automated tests alone.

Story 7.1 establishes the shared keyboard-focus, semantic navigation, decorative-icon, dynamic-control-state, and reduced-motion foundation. Story 7.2 connects authentication errors to invalid fields, adds shared polite status announcements for asynchronous follow actions and composer feedback, and removes duplicate follow-button request handlers. Story 7.3 audits representative creation, discovery, messaging, account, and moderation-adjacent templates for heading structure, control names, decorative content, table relationships, dynamic focus, and core text-token contrast. Story 7.4 adds deterministic reflow safeguards for narrow/zoomed layouts, removes remaining decorative timeline icon noise, maps current evidence to representative WCAG 2.2 criteria, and defines the explicit NVDA/VoiceOver and 200%/400% zoom evidence gate that must be completed before any conformance claim.

## Candidate Sprint 8 — Production launch path

Sprint 8 should be selected only after the manual Sprint 7 evidence gate is dispositioned and the infrastructure plan is refreshed against current requirements and costs.

**Candidate outcomes:**

- Reassess issue #16 and select the lowest-cost production architecture that satisfies current PostgreSQL/private-media/worker requirements
- Update Terraform/deployment design before provisioning any paid AWS resources
- Preserve separate Terraform `main.tf`, `variables.tf`, and `outputs.tf` responsibilities
- Keep optional paid infrastructure disabled until explicitly authorized
- Exercise the existing release-readiness, preflight, backup/restore, rollback, and destroy procedures against the selected environment
- Document actual recurring cost before apply

## Future backlog

Potential work after stabilization:

- Email ownership verification and further account-recovery hardening
- API design
- Search/discovery improvements
- Additional moderation tooling based on real community needs
- Theme and responsive UI refinement
- Creator/business product refinement based on measured usage
- Optional federation feasibility study
