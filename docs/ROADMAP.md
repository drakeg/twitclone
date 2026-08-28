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
- Email ownership verification, resend support, expiring signed verification links, recovery-token hardening, and reverification after an email change

## Sprint 6 — Deployment and operations readiness

**Goal:** Prepare a documented, low-cost deployment path.

**Status:** Completed through the application/operations readiness boundary.

Story 6.4 documents the durable-state boundary, recovery objectives, backup and restore rehearsal, rollback decision tree, and a dated low-traffic deployment estimate. Story 6.5 implements the selected private S3-compatible adapter while preserving local filesystem-backed Compose. Story 6.6 adds a dry-run-first, repeatable, content-verified command for migrating existing filesystem media to the configured private bucket. Story 6.7 adds a production-only deployment preflight that proves database connectivity, migration currency, and private media read/write/delete access before traffic is enabled. Story 6.8 supplies standard release-readiness and restore-rehearsal evidence records so every launch gate has an owner, timestamp, result, and reviewable disposition.

## Priority design sprint — UI cleanup and visual refresh

**Goal:** Make Ripple feel polished, welcoming, and easy to navigate.

**Status:** Completed. A shared visual system, responsive navigation, refreshed primary flows, and regression coverage are in place.

## Sprint 7 — Accessible interaction and content

**Goal:** Make Ripple's core flows understandable and operable with keyboards, assistive technology, zoom, and reduced-motion preferences.

**Status:** Automated/remediable implementation completed through Story 7.4. Manual assistive-technology evidence remains an explicit release gate; Ripple does not claim WCAG conformance from automated tests alone.

Story 7.1 establishes the shared keyboard-focus, semantic navigation, decorative-icon, dynamic-control-state, and reduced-motion foundation. Story 7.2 connects authentication errors to invalid fields, adds shared polite status announcements for asynchronous follow actions and composer feedback, and removes duplicate follow-button request handlers. Story 7.3 audits representative creation, discovery, messaging, account, and moderation-adjacent templates for heading structure, control names, decorative content, table relationships, dynamic focus, and core text-token contrast. Story 7.4 adds deterministic reflow safeguards for narrow/zoomed layouts, removes remaining decorative timeline icon noise, maps current evidence to representative WCAG 2.2 criteria, and defines the explicit NVDA/VoiceOver and 200%/400% zoom evidence gate that must be completed before any conformance claim.

## Sprint 8 — Production launch path

**Goal:** Turn the completed application/operations contracts into a low-cost, reproducible production deployment without provisioning unnecessary infrastructure.

**Status:** Repository-side zero-spend implementation completed through Story 8.8. Infrastructure remains plan/validate-only until explicit spend authorization. Ripple continues to run normally through the existing local Docker Compose stack.

Story 8.1 selects a low-traffic AWS topology in ADR-0044: one `t4g.small` EC2 application host, one private Single-AZ RDS PostgreSQL 18 `db.t4g.micro`, private encrypted/versioned S3 media, no NAT Gateway or load balancer, and optional Route 53 DNS. The planning estimate is approximately $31-$35/month before backups, domain, observability, email, and overages. Story 8.1 does **not** authorize an AWS apply or recurring spend.

Story 8.2 implements that topology as version-pinned Terraform under `infra/terraform`. Resource declarations, variables, and outputs remain separated; the application host uses an IAM instance role for private media; RDS and S3 remain private durable boundaries; optional Route 53 and Multi-AZ RDS are disabled by default; Terraform state/local inputs are excluded from source control; and production destroy paths are deliberately protected. Story 8.2 remains **plan/validate-only** and does not authorize `terraform apply` or recurring spend.

Story 8.3 defines a container-first production release contract without changing Ripple's everyday local workflow. `compose.production.yaml` separates one-shot migration and preflight jobs from Gunicorn, exactly one scheduled worker, and a Caddy TLS proxy; production secrets live in a host-only environment file; an immutable-image deployment wrapper provides validate/deploy/rollback actions; and the release script explicitly never runs Terraform.

Story 8.4 defines immutable release-image provenance without requiring a registry or AWS account. A clean checkout can build a SHA-tagged ARM64 image locally, the Docker image records OCI source/revision/creation labels, the build script verifies the revision label, `:latest` is rejected, and registry publication remains opt-in.

Story 8.5 prepares the future EC2 container host automatically while preserving the no-spend boundary. A checked-in Amazon Linux 2023 bootstrap installs Docker, installs checksum-verified Docker Compose, prepares locked-down Ripple runtime paths, and copies production deployment artifacts from an exact immutable Git commit. Terraform embeds that script as EC2 user data and blocks EC2 creation unless a 40-character `host_bootstrap_ref` is deliberately supplied.

Story 8.6 defines the production runtime-configuration handoff without provisioning a secrets service. A renderer validates required settings and writes the host-only environment file atomically with mode `0600`; the default source is the operator shell so the complete mechanism is testable today with zero AWS spend. A future opt-in SSM Parameter Store source reads the same named settings with decryption after AWS deployment is explicitly authorized.

Story 8.7 ties the release contracts together with a zero-spend operator dry run. `scripts/dry-run-production-release.sh` selects an immutable image, renders and validates a temporary production configuration, validates the production Compose model, and prints the exact migration/preflight/start/verification and rollback sequence without starting containers or contacting AWS.

Story 8.8 adds the final repository-side pre-apply gate. `scripts/check-aws-launch-readiness.sh structure` validates Terraform formatting/schema, required deployment artifacts, the zero-spend release dry run, and the absence of infrastructure-creation commands. A stricter future `launch` mode additionally requires a clean `main`, immutable release/bootstrap identifiers, a dated cost review, successful restore rehearsal, completed Sprint 7 accessibility evidence, a tested backup-alert path, and a prepared release record. Neither mode runs `terraform plan` or `terraform apply`, and neither authorizes AWS spend.

The manual Sprint 7 NVDA/VoiceOver and zoom evidence remains a public-launch gate even while Sprint 8 infrastructure work is otherwise ready.

## Product iteration after Sprint 8

Before the formal differentiation roadmap began, Ripple completed several user-facing refinements while AWS provisioning remained deferred:

- Email ownership verification and recovery hardening — completed, including reverification after a registered email address changes.
- Search/discovery refresh — completed. Search covers usernames, profile bios, normal post text, `@username`, and `#hashtag` queries while excluding removed posts and presenting clearer result states.
- Moderation queue triage — completed. Admins can prioritize pending reports, filter the queue, see status counts, and identify content with repeated reports while preserving individual reporter outcomes.
- Ripple+ profile/theme refinement — completed. Ripple+ members can visually preview curated themes, see the active theme on their public profile, and preserve the existing free-profile fallback.
- Creator/business refinement — completed through the current measured analytics slice. Creator Pro includes daily measured trends and a measured audience path from impressions to profile visits to net follower growth; these ratios remain aggregate observations rather than user-level attribution or causation claims.

## Sprint 9 — Intentional conversations

**Goal:** Differentiate Ripple through explicit conversational intent, constructive participation, evidence-backed community context, and author-controlled conversation health.

**Status:** Completed. Detailed acceptance and follow-on notes are maintained in `docs/sprints/SPRINT_9.md`.

Delivered capabilities include conversation-intent labels, intent-aware response guidance, Helpful/Thoughtful/Useful-context contribution signals, community fact/context submissions with independent consensus and appeals, transparent reviewer history, and Open/Closed plus Answered/Resolved conversation state. Resolved remains informational; closing is the explicit mechanism for preventing new quote responses.

# Forward differentiation roadmap

The following numbered sprints are the agreed product direction after Sprint 9. They are deliberately sequenced so later capabilities build on earlier data and behavior. A sprint's detailed `docs/sprints/SPRINT_N.md` file should be created when that sprint begins; future sprint definitions below are roadmap contracts rather than claims that implementation has started.

## Sprint 10 — Topic reputation and expertise

**Goal:** Help users find demonstrated topic-specific contributors without turning reputation into a global popularity score.

**Planned direction:**

- Define a transparent topic vocabulary using explicit user/post topics rather than inferred sensitive traits.
- Derive topic contribution history from real constructive signals and other eligible, auditable activity.
- Show explainable topic-specific reputation summaries such as contribution history and earned levels.
- Prevent self-awards, paid-status influence, follower-count influence, and hidden political/viewpoint scoring.
- Keep reputation informational initially; do not silently use it to amplify or suppress reach.
- Establish anti-gaming tests and clear reset/correction behavior before reputation affects higher-trust workflows.

## Sprint 11 — Collaborative knowledge and resource posts

**Goal:** Let useful community knowledge remain discoverable and maintainable instead of disappearing down a chronological feed.

**Planned direction:**

- Introduce a durable resource/guide content type separate from ordinary posts.
- Support attributable revisions and visible revision history.
- Allow source/reference links and structured topic association.
- Define contributor/reviewer permissions without allowing popularity or payment to purchase edit authority.
- Provide discovery paths from topics and relevant conversations to maintained resources.

## Sprint 12 — Feed choice and relationship-first discovery

**Goal:** Give users meaningful, understandable control over how Ripple orders and discovers content.

**Planned direction:**

- Preserve a straightforward chronological/following option.
- Add explicit topic-oriented and relationship-first/quiet discovery modes where useful.
- Explain what each feed mode optimizes for; avoid a single opaque engagement score.
- Keep user choice persistent and reversible.
- Measure only behavior Ripple actually records and avoid claims about emotional state or inferred ideology.

## Sprint 13 — Communities and topic spaces

**Goal:** Create persistent spaces where conversations, resources, and topic contribution history can coexist.

**Planned direction:**

- Community/topic-space membership and discovery.
- Space-specific posts and durable resources.
- Understandable community roles and moderation boundaries.
- Community-specific contribution context without replacing global Community Standards.
- Privacy-conscious local/community coordination may be evaluated here, with coarse/explicit location rather than hidden precise tracking.

## Sprint 14 — Replies and conversation structure

**Goal:** Add a true public reply model so Ripple conversations can develop as readable discussions rather than relying on Quote as the only public response mechanism.

**Planned direction:**

- Threaded replies with stable URLs and authorization/visibility rules.
- Conversation intent and health controls applied coherently to replies.
- Constructive contribution signals and community context integrated where semantically appropriate.
- Existing Quote behavior retained as a distinct repost-with-comment action.
- Migration/compatibility must not falsely reinterpret historical Quotes as replies.

## Sprint 15 — Creator and community sustainability

**Goal:** Expand sustainable creator/community value without selling credibility, moderation influence, or organic reach.

**Planned direction:**

- Evaluate memberships/support and creator/community convenience tools.
- Extend measured analytics only where Ripple has reliable underlying data.
- Keep core conversation, safety, community participation, and reputation available without pay-to-win mechanics.
- Document fees, entitlements, cancellation behavior, and moderation boundaries before enabling any new paid capability.

## Sprint 16 — Public API and integrations

**Goal:** Provide a stable, permissioned interface for automation and external clients without exposing internal implementation details as an accidental API.

**Planned direction:**

- Versioned API contracts for selected mature capabilities.
- Scoped authentication/authorization and rate limiting.
- Developer documentation and representative contract tests.
- Webhook/integration feasibility for appropriate events.
- Privacy, abuse, and operational-cost review before broad write access.

## Sprint 17 — Federation and interoperability feasibility

**Goal:** Decide whether federation/interoperability materially advances Ripple's product goals before committing to a distributed architecture.

**Status:** Decision sprint only; implementation is not pre-authorized.

**Planned direction:**

- Evaluate ActivityPub and relevant interoperability approaches against Ripple's identity, moderation, community-context, privacy, and conversation-control semantics.
- Model abuse handling, deletion, blocking, moderation authority, media storage, and operating cost across server boundaries.
- Produce an ADR with proceed/defer/reject recommendation and an incremental implementation plan only if justified.
- Do not add recurring infrastructure or operational burden merely to claim federation support.

## Cross-cutting release gates and deferred work

These are not new product sprints and remain independently tracked:

- **AWS activation:** Sprint 8 remains plan/validate-only. No `terraform apply`, paid AWS activation, or recurring spend is authorized until explicitly approved.
- **Accessibility evidence:** Manual NVDA/VoiceOver and 200%/400% zoom evidence from Sprint 7 remains a public-launch/conformance gate.
- **Production evidence:** Restore rehearsal, backup-alert path, cost review, immutable release identifiers, and release record remain part of the launch readiness contract.
- **Usage-driven refinements:** Search, moderation, themes, creator analytics, community-context source quality, anti-brigading, and conversation-state history may receive targeted follow-up when real usage provides evidence for the change.

## Roadmap governance

- `docs/ROADMAP.md` is the authoritative numbered product roadmap.
- Detailed sprint documents live under `docs/sprints/` and are created/updated when a sprint becomes active.
- Completed sprint documentation is historical evidence and should not be rewritten to imply unimplemented features were delivered.
- Sprint scope can be refined before implementation, but once a sprint begins its goal and acceptance criteria should remain stable unless an explicit documented decision changes them.
- New infrastructure spend, paid third-party services, or AWS activation require explicit authorization separate from roadmap inclusion.
