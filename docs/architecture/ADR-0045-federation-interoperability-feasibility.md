# ADR-0045: Federation and interoperability feasibility

- Status: Accepted — defer broad federation
- Date: 2026-09-13
- Sprint: 17
- Decision type: Feasibility / architecture boundary

## Context

Ripple now has mature local semantics for identity, chronological and relationship-first feeds, explicit topics, community spaces, threaded replies, conversation intent and health controls, constructive contribution signals, moderation, creator/community sustainability foundations, and a versioned public API.

The roadmap therefore requires a deliberate decision before introducing a distributed social architecture. The question is not whether Ripple *can* emit ActivityStreams JSON, but whether cross-server federation can preserve Ripple's product and safety semantics without imposing disproportionate operational cost or creating misleading guarantees.

ActivityPub is a W3C Recommendation built on ActivityStreams 2.0. Major implementations such as Mastodon use it for profile discovery, follows, posts, boosts, likes, deletes, reports, blocking, polls, and other interactions. In practice, interoperable behavior also depends on implementation-specific conventions and extensions, signed HTTP requests, remote-domain moderation, media handling, delivery queues, retries, and local policy decisions.

## Decision

**Defer broad ActivityPub federation. Do not implement server-to-server federation in the current roadmap.**

Ripple should continue to improve interoperability through stable public contracts that do not require distributed state ownership. The existing versioned API, exportable public URLs, stable resource identifiers, webhook contract work, and explicit domain semantics are the appropriate foundation today.

This is a **defer**, not a permanent rejection. A later federation implementation may be reconsidered when product demand, moderation staffing, operational capacity, and measured usage justify the distributed complexity.

No federation code, remote inbox/outbox processing, WebFinger endpoint, HTTP-signature machinery, remote actor persistence, remote media ingestion, delivery worker, federation queue, or recurring infrastructure is authorized by this ADR.

## Why broad federation is deferred

### 1. Ripple semantics do not map cleanly to generic remote objects

Ripple distinguishes ordinary posts, reposts, quotes, public threaded replies, space-scoped conversations, durable resources, community context, conversation intent, Closed state, Answered/Resolved state, topic reputation, and local constructive contribution signals.

A remote server may understand only a subset of these concepts. Flattening them into generic `Note`, `Announce`, or extension objects could cause semantic loss; treating remote servers as if they enforce Ripple-specific controls would create false expectations.

Examples:

- A Ripple conversation marked **Closed** can block new local replies, but a remote server cannot be assumed to prevent its users from creating a new object that references the original post.
- **Answered / Resolved** is informational and reversible locally; remote software may ignore it entirely.
- Ripple community-space roles, local moderation decisions, and contribution context are local authority and must not become portable claims of global status.
- Constructive signals and topic reputation should not silently federate as universal reputation scores.

### 2. Moderation authority becomes distributed

Federated moderation is inherently multi-authority. A local block or limit does not guarantee equivalent treatment on another server. Remote software may continue to display cached public content or apply different moderation rules.

Ripple currently provides understandable local moderation boundaries. Broad federation would require new user-facing language explaining that local removal, blocking, closure, and community actions cannot guarantee deletion or suppression on independently operated servers.

### 3. Deletion and data lifecycle guarantees become weaker

ActivityPub supports `Delete`, but delivery is asynchronous and remote servers control their own persistence. Ripple cannot honestly promise that a remote operator will immediately erase previously delivered public content, cached media, or derived metadata.

Before federation, Ripple would need explicit product language and retention rules distinguishing:

- local deletion;
- best-effort federation deletion delivery;
- remote cache persistence;
- account deletion;
- domain suspension;
- media lifecycle;
- legal/privacy erasure workflows.

### 4. Blocking and privacy semantics are not universal guarantees

Remote blocking behavior varies by implementation. Some systems send extension behavior beyond the ActivityPub core model, and signed/authorized fetch modes can alter what remote servers can retrieve.

Ripple must not present federation blocking as a cryptographic privacy boundary. Public federation should be treated as public distribution unless a later design proves stronger end-to-end semantics.

### 5. Media increases cost and abuse surface

Remote media introduces bandwidth, storage, malware/content-processing, takedown, cache-invalidation, and moderation concerns. Mirroring remote media would weaken the current low-cost deployment plan unless bounded carefully; hot-linking remote media creates availability and privacy tradeoffs.

No remote-media ingestion should be added without a separate storage, abuse, retention, and cost design.

### 6. Reliable federation requires new asynchronous operations

A production federation implementation needs durable delivery state, retry/idempotency behavior, signing keys, remote endpoint validation, SSRF protection, backoff, queue recovery, observability, dead-letter handling, domain controls, and operational tooling.

Ripple's current low-cost production topology deliberately avoids unnecessary distributed infrastructure. Federation should not force recurring operational burden merely to claim protocol support.

## Interoperability direction that remains approved

Ripple may continue to improve low-risk interoperability that does not create distributed social-state ownership. Suitable work includes:

1. Stable, versioned public API contracts.
2. Stable public permalinks and canonical identifiers.
3. User-controlled export of their own posts, replies, profile data, follows, bookmarks, and other eligible account data.
4. Machine-readable public metadata where useful.
5. Provider-neutral webhook contracts that remain behind their existing activation gates.
6. Import/export tooling with explicit provenance and conflict behavior.
7. Mapping documentation showing how Ripple concepts *could* correspond to ActivityStreams types without activating federation.

These capabilities improve portability and future readiness while keeping current moderation and data ownership boundaries understandable.

## Reconsideration gates

Broad federation should be reconsidered only when all of the following have evidence, not assumptions:

- Clear user demand for cross-server following and conversation.
- A stable mapping for posts, reposts, quotes, replies, polls, spaces, resources, and visibility states.
- A written policy for what does **not** federate, especially community context, contribution signals, moderation authority, paid status, and local reputation.
- Remote-account identity and impersonation handling.
- WebFinger/actor discovery and canonical-domain rules.
- HTTP-signature/key-rotation design.
- SSRF-safe remote fetch and inbox validation.
- Durable inbox/outbox persistence with idempotency and bounded retries.
- Domain allow/block/suspend operations and audit history.
- Deletion/account-removal semantics that explicitly describe best-effort remote behavior.
- Remote-media policy and measured storage/bandwidth cost.
- Abuse/spam-rate controls for remote activity.
- Moderation staffing and operational ownership.
- Backup/recovery and queue-replay evidence.
- A dated deployment-cost estimate and explicit spend authorization if new infrastructure is required.

## Incremental implementation plan if reconsidered

If the gates above are later satisfied, implementation should be staged rather than enabling full federation at once:

1. **Read-only actor discovery prototype** — WebFinger and public Actor representation, no remote follows or inbox processing.
2. **Outbound public-post compatibility prototype** — map a minimal public post subset to ActivityStreams without receiving remote activity.
3. **Controlled test federation** — isolated development environment with allow-listed test domains only.
4. **Remote follow lifecycle** — explicit Follow/Accept/Reject/Undo semantics and local audit state.
5. **Inbox/outbox reliability layer** — durable delivery, signatures, replay protection, SSRF controls, retries, observability, and operator tooling.
6. **Moderation/deletion hardening** — domain actions, remote reports, removal semantics, account deletion, and media policy.
7. **Limited production pilot** — opt-in users and allow-listed peers with measured abuse, queue, storage, bandwidth, and support costs.
8. **General availability decision** — only after evidence from the pilot.

Each phase requires a separate implementation authorization. None is pre-authorized by Sprint 17.

## Alternatives considered

### Proceed directly with full ActivityPub federation

Rejected for now. The protocol is viable, but Ripple's current product semantics and low-cost operations model would require substantial new policy and infrastructure work before broad federation could be represented safely and accurately.

### Permanently reject federation

Rejected. Open interoperability remains strategically useful, and Ripple's versioned API plus stable local domain model create a reasonable foundation for future reconsideration.

### Implement only a compatibility façade immediately

Deferred. Even apparently read-only ActivityPub surfaces create identity/canonical-URL expectations and can become externally depended upon. They should be introduced only as an intentional product contract.

## Consequences

### Positive

- Preserves Ripple's understandable local moderation and conversation-control semantics.
- Avoids premature distributed operational cost.
- Prevents community context, local reputation, paid status, or moderation authority from being misrepresented as portable global truth.
- Keeps future ActivityPub adoption possible through staged gates.
- Aligns with the existing no-spend infrastructure policy.

### Negative

- Ripple users cannot yet follow or interact directly with ActivityPub users on other servers.
- Future federation work will require significant architecture and policy effort.
- Some interoperability value remains unrealized until product demand justifies the cost.

## Result

Sprint 17 concludes with **DEFER BROAD FEDERATION** and **CONTINUE LOW-RISK INTEROPERABILITY FOUNDATIONS**.

No distributed federation implementation is authorized at this time.
