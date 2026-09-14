# Sprint 17 — Federation and Interoperability Feasibility

**Status:** Completed — decision sprint only.

## Goal

Decide whether federation/interoperability materially advances Ripple's product goals before committing to a distributed architecture.

## Decision

**Defer broad federation. Continue low-risk interoperability foundations.**

Sprint 17 does not authorize ActivityPub server-to-server implementation, new federation infrastructure, recurring spend, or remote social-state persistence.

The decision is recorded in [`ADR-0045-federation-interoperability-feasibility.md`](../architecture/ADR-0045-federation-interoperability-feasibility.md).

## Evaluation summary

ActivityPub remains the most relevant open social-federation protocol for Ripple because it is a W3C Recommendation built on ActivityStreams 2.0 and is widely implemented across federated social software.

However, practical federation is more than serializing posts. A production implementation would introduce cross-server identity, discovery, signatures, inbox/outbox delivery, retries, blocking, deletion, moderation, media, remote caching, domain policy, abuse controls, and operational ownership.

Ripple also has product semantics that do not map cleanly to universal remote guarantees:

- conversation intent;
- Closed versus Answered / Resolved state;
- public replies versus Quotes;
- topic-specific contribution reputation;
- community-space roles and local moderation;
- constructive contribution signals;
- durable resources;
- paid/supporter state that must not become credibility or reach;
- global versus space-scoped visibility.

A remote server may ignore or reinterpret those concepts. Ripple therefore must not imply that local moderation, closure, deletion, or reputation semantics are globally enforced.

## Story 17.1 — Protocol and semantic fit

**Status:** Completed.

- Evaluated ActivityPub/ActivityStreams as the primary federation candidate.
- Mapped Ripple's mature public-social concepts against likely federation primitives.
- Identified semantic-loss boundaries for conversation health, spaces, community context, resources, and contribution reputation.
- Determined that a minimal `Person` / `Note` / `Follow` mapping is technically plausible but insufficient to preserve Ripple's full semantics.

## Story 17.2 — Identity, blocking, deletion, and moderation authority

**Status:** Completed.

- Distinguished local enforcement from remote-server behavior.
- Recorded that local blocking or moderation cannot guarantee equivalent remote treatment.
- Recorded that deletion delivery is best-effort across independent servers and cannot be represented as guaranteed remote erasure.
- Preserved Ripple Community Standards and space moderation as local authority rather than portable global claims.
- Identified remote identity, impersonation, key rotation, domain moderation, and report handling as required future design work.

## Story 17.3 — Media, privacy, abuse, and operating cost

**Status:** Completed.

- Identified remote-media storage/hot-linking tradeoffs, takedown obligations, bandwidth/storage growth, and cache behavior.
- Identified SSRF-safe remote fetch, signed delivery, replay protection, spam/rate limiting, durable retries, queue recovery, and observability as prerequisites.
- Confirmed that the current low-cost production topology should not be expanded merely to claim federation support.
- Existing no-AWS-activation and no-recurring-spend boundaries remain unchanged.

## Story 17.4 — Interoperability alternatives

**Status:** Completed.

Approved direction without federation activation:

- continue versioned public API contracts;
- preserve stable canonical public URLs;
- add user-controlled account/data export where useful;
- maintain provider-neutral webhook contracts behind their existing activation gate;
- consider machine-readable public metadata and import/export tooling with explicit provenance;
- document future ActivityStreams mappings without advertising unsupported federation behavior.

## Story 17.5 — Architecture decision and future gates

**Status:** Completed.

ADR-0045 records the final recommendation:

- **DEFER** broad ActivityPub federation;
- do **not** permanently reject federation;
- continue low-risk interoperability foundations;
- require explicit evidence gates before any future federation implementation;
- if reconsidered, stage the work from read-only discovery through controlled allow-listed testing before any general production availability.

No implementation phase is pre-authorized.

## Reconsideration criteria

A future sprint may reopen federation only when there is evidence for:

- meaningful user demand for cross-server interaction;
- stable mappings for Ripple's public content and visibility semantics;
- explicit non-federation boundaries for community context, moderation authority, paid status, and local reputation;
- remote identity and impersonation handling;
- signatures and key rotation;
- SSRF-safe remote fetch;
- durable inbox/outbox idempotency and retry behavior;
- domain moderation tooling;
- deletion/account-removal policy;
- remote-media policy and measured cost;
- remote abuse/spam controls;
- operational ownership and moderation staffing;
- recovery/replay evidence;
- dated cost review and separate spend authorization where required.

## Sprint outcome

Sprint 17 completed the federation feasibility decision without introducing distributed architecture.

Ripple's current product direction remains a centrally operated service with open, versioned interoperability surfaces. Broad ActivityPub federation is deferred until product demand and operational evidence justify the additional identity, moderation, privacy, media, delivery, and cost complexity.

## Definition of done

Completed. The repository now contains a documented proceed/defer/reject decision, explicit semantic and operational risk analysis, a future gated implementation sequence, and a clear statement that federation code and recurring infrastructure are not authorized by this sprint.
