# Sprint 16 — Public API and Integrations

**Status:** Completed.

## Goal

Provide a stable, permissioned interface for automation and external clients without exposing Ripple's internal implementation details as an accidental API.

## Product principles

- Every public endpoint is explicitly versioned and documented.
- Public responses expose bounded contract fields rather than serializing ORM models.
- Visibility rules fail closed; content that is removed, scheduled for the future, or scoped outside the global public surface must not leak through the API.
- Write access uses explicit scoped bearer credentials; session cookies are not treated as an API credential strategy.
- Rate limiting, token scope, revocation, auditability, abuse controls, and operational cost precede broader write access.
- API access does not purchase ranking, reputation, verification, moderation authority, or safety exceptions.
- Existing AWS/no-spend restrictions remain unchanged.

## Story 16.1 — Versioned read-only API foundation

**Status:** Completed in PR #229.

- Adds `/api/v1`, bounded public post reads, and fail-closed visibility behavior.
- Exposes no email, admin, entitlement, moderation, or ORM-internal state.

## Story 16.2 — Scoped API authentication and revocation

**Status:** Completed in PR #230.

- Adds hashed-at-rest, expiring, revocable bearer credentials with explicit scopes.
- Browser sessions do not authenticate protected API operations.
- Operator CLI manages credentials without redisplaying raw secrets.

## Story 16.3 — Rate limiting and abuse boundaries

**Status:** Completed in PR #231.

- Adds database-backed fixed-window limits for public reads, invalid-token attempts, and valid credentials.
- Hashes public-client identifiers before persistence and never stores raw bearer material in rate-limit state.
- Documents privacy, operational, abuse, and cost boundaries.

## Story 16.4 — Mature read/write resource contracts

**Status:** Completed in PR #232.

- Preserves bounded public `GET /api/v1/posts/<id>` reads.
- Adds explicit `posts:write` scope and bounded `POST /api/v1/posts` creation.
- Reuses Ripple validation, conversation-intent normalization, topic associations, mention notifications, and visibility/moderation behavior.
- Read-only credentials fail closed on write operations.
- API-created posts do not gain ranking, reputation, verification, moderation, entitlement, or paid-reach advantages.
- `docs/API_RESOURCE_CONTRACTS.md` records supported and excluded behavior.

## Story 16.5 — Webhooks and integration contract

**Status:** Completed in this story.

### Decision

Ripple now has a provider-neutral **contract-only** webhook foundation, but outbound delivery remains disabled until a later activation story satisfies the reliability, privacy, SSRF, secret-management, persistence, recovery, and cost gates documented in `docs/API_WEBHOOKS.md`.

### Implemented contract

- Initial allow-listed event type: `post.created`.
- Versioned event envelope with stable event ID, type, UTC occurrence time, version, and bounded data object.
- Stable event ID is the consumer idempotency key and must remain unchanged across retries.
- Deterministic canonical JSON body for signing.
- Timestamped HMAC-SHA-256 signature format: `t=<unix>,v1=<digest>`.
- Five-minute default replay window.
- Verification accepts multiple `v1` signatures to support bounded secret-rotation overlap.
- Proposed bounded retry schedule: 1 minute, 5 minutes, 30 minutes, 2 hours, and 6 hours.
- Unsupported event types fail closed.
- Focused regression tests cover envelope stability, deterministic payloads, valid signatures, tampering, wrong secrets, replay rejection, rotation overlap, and retry bounds.

### Activation boundary

This story does **not** persist subscriber endpoints, perform outbound HTTP, create delivery/outbox tables, activate a worker, add a managed queue, call a third-party webhook service, activate AWS resources, or authorize recurring spend.

Before outbound delivery can be enabled, a later story must provide endpoint ownership/authorization, HTTPS and SSRF controls, encrypted secret persistence/rotation, reliable outbox semantics, idempotent worker retries, bounded logging/retention, disable/delete lifecycle, recovery/replay procedures, observability without secret leakage, and measured operational/cost evidence.

## Definition of done

Sprint 16 is complete: Ripple has a documented versioned API, scoped/revocable authentication, rate/abuse controls, representative stable read/write resource contracts, and a tested webhook integration decision with explicit privacy, reliability, replay, rotation, retention, activation, and cost boundaries.
