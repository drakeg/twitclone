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

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_10.md`.

Delivered capabilities include explicit normalized topics, auditable topic contribution evidence, explainable profile summaries, transparent contributor discovery, correction behavior, and anti-gaming boundaries. Reputation remains topic-specific and informational; payment, follower count, verification, and hidden sensitive-trait inference do not buy reputation or feed reach.

## Sprint 11 — Collaborative knowledge and resource posts

**Goal:** Let useful community knowledge remain discoverable and maintainable instead of disappearing down a chronological feed.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_11.md`.

Delivered capabilities include durable resource posts, attributable append-only revisions, visible history, source/reference support, explicit topic association, topic discovery, and non-destructive resource removal that preserves provenance. Popularity and paid status do not purchase edit authority or discovery placement.

## Sprint 12 — Feed choice and relationship-first discovery

**Goal:** Give users meaningful, understandable control over how Ripple orders and discovers content.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_12.md`.

Delivered feed modes include All Ripple, Following, Topic, and relationship-first Quiet mode with understandable ordering, persistent/reversible user choice where appropriate, and regression-tested integrity boundaries. Engagement totals, payment, verification, follower count, inferred ideology, and sensitive traits do not silently reorder organic content.

## Sprint 13 — Communities and topic spaces

**Goal:** Create persistent spaces where conversations, resources, and topic contribution history can coexist.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_13.md`.

Delivered capabilities include persistent public spaces, explicit membership and roles, space-scoped conversations/resources, auditable local moderation and appeals, and descriptive community contribution context. Global Community Standards remain authoritative, and community roles/payment do not create global ranking or reputation authority.

## Sprint 14 — Replies and conversation structure

**Goal:** Add a true public reply model so Ripple conversations can develop as readable discussions rather than relying on Quote as the only public response mechanism.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_14.md`.

Delivered capabilities include threaded replies with stable URLs, deterministic ordering, conversation-intent and health integration, reply-level constructive signals/moderation, bounded deep-thread handling, removal-safe tombstones, and compatibility rules that preserve historical Quotes as a distinct repost-with-comment action.

## Sprint 15 — Creator and community sustainability

**Goal:** Expand sustainable creator/community value without selling credibility, moderation influence, or organic reach.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_15.md`.

Delivered work includes reversible creator-support and membership-publication foundations, measured sustainability-page analytics, and a provider-neutral transaction contract for possible future checkout. Actual payment processing remains separately gated and unimplemented; payment cannot purchase reach, moderation authority, verification, reputation, or safety exceptions.

## Sprint 16 — Public API and integrations

**Goal:** Provide a stable, permissioned interface for automation and external clients without exposing internal implementation details as an accidental API.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_16.md`.

Delivered capabilities include versioned bounded API contracts, scoped/revocable bearer credentials, database-backed rate limiting, representative stable read/write post contracts, and a tested provider-neutral webhook envelope/signature/retry design. Outbound webhook delivery remains deliberately inactive pending endpoint ownership, SSRF, outbox/retry, observability, retention, and cost controls.

## Sprint 17 — Federation and interoperability feasibility

**Goal:** Decide whether federation/interoperability materially advances Ripple's product goals before committing to a distributed architecture.

**Status:** Completed — decision sprint only. Detailed findings are maintained in `docs/sprints/SPRINT_17.md` and ADR-0045.

Decision: **defer broad ActivityPub federation and continue low-risk interoperability foundations**. Ripple does not currently authorize remote inbox/outbox processing, remote social-state persistence, remote media ingestion, federation delivery workers, or recurring federation infrastructure. Reconsideration requires explicit product demand plus identity, moderation, privacy, deletion, media, abuse, reliability, staffing, recovery, and cost evidence.

## Sprint 18 — User-controlled portability

**Goal:** Continue low-risk interoperability by giving people useful exports of their Ripple identity and authored work without activating federation or adding infrastructure spend.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_18.md`.

Delivered capabilities include a versioned provider-neutral JSON export, requester-visible direct-message portability, subscription/entitlement metadata without provider secrets, an owned-media reference manifest without packaged bytes, and a non-mutating import/provenance compatibility contract. Import writes remain disabled. Packaged media and actual import execution require separately authorized future work.

## Sprint 19 — Launch readiness evidence

**Goal:** Make Ripple's existing public-launch prerequisites visible as a clear, auditable, zero-spend readiness status without provisioning infrastructure or weakening the authoritative launch gate.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_19.md`.

Delivered capabilities include read-only human/JSON readiness reporting, sanitized evidence-record metadata, advisory freshness review, versioned readiness snapshots, and deterministic SHA-256 integrity verification. The authoritative Sprint 8 launch gate remains unchanged. No AWS calls, Terraform apply, provisioning, signing infrastructure, or spend authorization were added.

## Sprint 20 — Dependency health and upgrade safety

**Goal:** Keep Ripple's runtime and dependency upgrade process explicit, reproducible, and aligned across local development, CI, release images, and automated update tooling.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_20.md`.

Delivered capabilities include an enforced Python 3.12 runtime contract, an explicit direct-dependency manifest plus checked-in lock validation, local dependency-surface inventorying, and conservative Renovate patch grouping with auto-merge disabled. Automatic lock generation remains deliberately deferred until a pinned compiler/resolver workflow and security-bot interaction can be specified and proven reproducible.

## Sprint 21 — Author-controlled post lifecycle

**Goal:** Give authors safe, understandable control over the lifecycle of their own original posts without weakening ownership, moderation, conversation-history, or topic-integrity boundaries.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_21.md`.

Delivered capabilities include owner-only editing of published original-post text, visible edit state, deterministic reconciliation of text-derived mentions/topics, and owner-requested soft removal that preserves relational and moderation history. Full post revision history is deliberately deferred until a concrete product, moderation, portability, or compliance requirement needs prior wording.

## Sprint 22 — Lifecycle contract consistency

**Goal:** Keep Ripple's external and portable representations aligned with user-visible content lifecycle semantics so editing/removal state does not exist only in the browser UI.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_22.md`.

Delivered capabilities include nullable edit state in the public API, portability schema evolution through v6, non-sensitive removal origin for exported authored content, and backward-recognizable v4/v5/v6 compatibility review with import writes still disabled. The sprint deliberately avoids propagating lifecycle fields into unrelated contracts without a concrete consumer need.

## Sprint 23 — API post lifecycle parity

**Goal:** Let authorized API clients manage the lifecycle of their own globally public original posts under the same safety and history semantics already established for the browser workflow.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_23.md`.

Delivered capabilities include bounded owner-only API editing and soft removal under `posts:write`, reuse of browser validation/mention/topic semantics, preserved non-public-post privacy, existing credential rate limits, and strong ETag/`If-Match` lost-update protection for lifecycle mutations. POST idempotency remains deliberately deferred until a concrete integration needs safe create retries.

## Sprint 24 — Local release-image serving confidence

**Goal:** Verify the immutable production image can actually serve HTTP through Gunicorn, not merely import the app module, without requiring AWS, public ports, or a production database.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_24.md`.

Delivered capabilities include an isolated launch of the immutable runtime image's production Gunicorn process, bounded polling of the database-independent `/health/live` route from inside the container, response validation, failure log capture, and guaranteed cleanup. No host port, image publication, AWS access, production database, or deployment authorization is involved.

## Sprint 25 — Accessibility evidence capture

**Goal:** Make Ripple's remaining manual accessibility release gate reproducible and reviewable without pretending automated checks establish conformance.

**Status:** Completed. Detailed implementation and boundaries are maintained in `docs/sprints/SPRINT_25.md`.

Delivered capabilities include a sanitized evidence-record template for the required NVDA, VoiceOver, and 200%/400% zoom scenarios, offline structural/completeness validation, defect/retest handling, release identity checks, and regression coverage that preserves the boundary between evidence validation and actual accessibility testing. Manual evidence collection remains a separate public-launch gate.

## Sprint 26 — Space ownership and membership administration

**Goal:** Make persistent Ripple Spaces operationally sustainable by giving owners safe handoff and member-administration workflows.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_26.md`.

Story 26.1 adds safe ownership transfer between existing Space members so a community is not permanently tied to its original creator. Follow-up stories cover owner-controlled member removal and durable membership-administration history while preserving Ripple's existing global moderation, reputation, verification, and monetization boundaries.

## Sprint 27 — Space invitations and access control

**Goal:** Add consent-based Space invitations and build the access-control foundation for private communities.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_27.md`.

Story 27.1 adds existing-user invitations that require explicit recipient acceptance before membership is created. Follow-up stories add operator invitation management and private Space visibility while preserving public Spaces and Ripple-wide safety/ranking boundaries.

## Sprint 28 — Space settings and lifecycle

**Goal:** Add safe owner-controlled settings and reversible lifecycle controls for persistent Spaces.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_28.md`.

Delivered capabilities include owner-only settings for name/description/visibility, reversible archive/restore behavior, participation freezes while archived, and owner-only lifecycle audit history that survives actor-account deletion without mixing lifecycle events into moderation or membership-administration histories.

## Sprint 29 — Space member operations

**Goal:** Make day-to-day Space membership administration efficient as communities grow beyond a small recent-member list.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_29.md`.

Delivered capabilities include an operator-only searchable/filterable paginated member roster, owner role/removal actions that reuse audited administration behavior, preserved filter/page context, moderator read-only access, and edge-case regression coverage without exposing private member data or creating ranking/scoring surfaces.

## Sprint 30 — Space conversation curation

**Goal:** Give Space operators lightweight tools to keep important community conversations visible without turning curation into paid reach or global ranking authority.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_30.md`.

Delivered capabilities include Space-local operator pin/unpin, deterministic pinned-first ordering, dedicated curation audit history, moderation-safe automatic unpin, archive safeguards, and regression coverage preserving global Tweet/feed/reputation/paid-reach boundaries.

## Sprint 31 — Private Space membership requests

**Goal:** Let people express interest in joining private Spaces without requiring operators to guess whom to invite, while keeping membership approval explicitly operator-controlled.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_31.md`.

Delivered capabilities include a privacy-preserving request-access surface, operator approve/deny review, all-operator notifications, shareable operator request links, durable resolution audit, and invitation/request state reconciliation without exposing private content or creating automatic approvals.

## Sprint 32 — Space membership reporting and export

**Goal:** Give Space operators a practical, portable view of membership operations without exporting private account data or turning the roster into a ranking surface.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_32.md`.

Delivered capabilities include an operator-only bounded CSV export using roster search/role filters, public username/Space role/explicit UTC join timestamp only, spreadsheet-formula neutralization, private/non-cacheable downloads, deterministic ordering, exact size-bound handling, archived-Space reporting, and regression coverage proving export does not mutate membership or audit state.

## Sprint 33 — Space announcements and operator communication

**Goal:** Give Space operators durable member communication without turning announcements into global-feed reach, ranking authority, or paid distribution.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_33.md`.

Delivered capabilities include persistent member-only operator announcements, non-destructive edit/withdraw/restore with prior/new wording audit history, bounded operator lifecycle history, lightweight per-member read state created only on member action, archived-Space read continuity, and regression boundaries preventing notification fanout, global-feed placement, ranking/reputation effects, verification effects, or paid reach.

## Sprint 34 — Space events and meetups

**Goal:** Give Space operators a durable, timezone-safe way to schedule member meetups without introducing global-feed promotion, paid reach, or external calendar infrastructure.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in `docs/sprints/SPRINT_34.md`.

Delivered capabilities include persistent member-only upcoming events, explicit IANA timezone input with UTC storage and DST ambiguity/nonexistence rejection, non-destructive edit/cancel/restore with attributable audit history, lightweight member Going/Maybe RSVP state with aggregate-only counts, archived-Space safeguards, and regression boundaries preventing notification fanout, global-feed promotion, ranking/reputation effects, verification effects, or paid reach.

## Sprint 35 — Space calendar portability

**Goal:** Make Space events portable to members' existing calendar workflows without requiring Ripple to operate an external calendar service or expose attendee/private member data.

**Status:** Completed. Detailed acceptance and implementation notes are maintained in docs/sprints/SPRINT_35.md.

Delivered capabilities include private member-only full and single-event iCalendar downloads for upcoming active Space events, shared stable UIDs, UTC timestamps, escaped text, UTF-8-aware line folding, bounded chronological output, archived-Space read continuity, private/no-store response handling, and regression coverage excluding attendee/RSVP/private member data.

## Sprint 36 — Space member directory and privacy

**Goal:** Give current Space members a useful people directory while treating Space membership association as private by default.

**Status:** In progress. Detailed acceptance and implementation notes are maintained in docs/sprints/SPRINT_36.md.

Story 36.1 adds a member-only opt-in directory with per-Space membership visibility defaulting off, public username/bio/role only, case-insensitive search, deterministic pagination, and archived-Space privacy continuity.

## Cross-cutting release gates and deferred work

These are not new product sprints and remain independently tracked:

- **AWS activation:** Sprint 8 repository-side implementation is complete. Live activation remains separately gated: no real AWS plan/apply, paid activation, or recurring spend is authorized until explicitly approved. The handoff sequence and live evidence boundary are documented in `docs/aws-activation-handoff.md`.
- **Accessibility evidence:** Manual NVDA/VoiceOver and 200%/400% zoom evidence from Sprint 7 remains a public-launch/conformance gate.
- **Production evidence:** Restore rehearsal, backup-alert path, cost review, immutable release identifiers, and release record remain part of the launch readiness contract.
- **Usage-driven refinements:** Search, moderation, themes, creator analytics, community-context source quality, anti-brigading, and conversation-state history may receive targeted follow-up when real usage provides evidence for the change.

## Roadmap governance

- `docs/ROADMAP.md` is the authoritative numbered product roadmap.
- Detailed sprint documents live under `docs/sprints/` and are created/updated when a sprint becomes active.
- Completed sprint documentation is historical evidence and should not be rewritten to imply unimplemented features were delivered.
- Sprint scope can be refined before implementation, but once a sprint begins its goal and acceptance criteria should remain stable unless an explicit documented decision changes them.
- New infrastructure spend, paid third-party services, or AWS activation require explicit authorization separate from roadmap inclusion.
