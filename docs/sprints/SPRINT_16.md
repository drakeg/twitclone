# Sprint 16 — Public API and Integrations

**Status:** In implementation.

## Goal

Provide a stable, permissioned interface for automation and external clients without exposing Ripple's internal implementation details as an accidental API.

## Product principles

- Every public endpoint is explicitly versioned and documented.
- Public responses expose bounded contract fields rather than serializing ORM models.
- Visibility rules fail closed; content that is removed, scheduled for the future, or scoped outside the global public surface must not leak through the API.
- Write access requires a separately designed scoped-authentication contract; session cookies are not treated as an API credential strategy.
- Rate limiting, token scope, revocation, auditability, abuse controls, and operational cost must be specified before broad write access.
- API access does not purchase ranking, reputation, verification, moderation authority, or safety exceptions.
- Existing AWS/no-spend restrictions remain unchanged.

## Story 16.1 — Versioned read-only API foundation

**Status:** In implementation.

- Adds a dedicated `api_v1` Flask blueprint mounted at `/api/v1`.
- `GET /api/v1/` exposes API name, version, and read-only-preview status.
- `GET /api/v1/posts/<id>` exposes one globally public post through a bounded JSON contract.
- Removed, future-scheduled, and Ripple Space-scoped posts fail closed as `post_not_found`.
- The endpoint is read-only and exposes no email, admin, entitlement, moderation, or ORM-internal state.
- No token, API key, OAuth, write endpoint, webhook, migration, paid service, or infrastructure activation is introduced.

### Acceptance criteria

- API routes are namespaced under `/api/v1`.
- Public post responses have deterministic documented fields.
- Removed, future-scheduled, and Space-scoped posts cannot be retrieved.
- Unsupported writes do not mutate posts.
- Tests cover metadata, serialization, visibility boundaries, Space isolation, and read-only behavior.

## Story 16.2 — Scoped API authentication and revocation

**Status:** Planned.

Define and implement a first-party API credential model with explicit scopes, secure token storage, revocation, expiration policy, and auditability.

## Story 16.3 — Rate limiting and abuse boundaries

**Status:** Planned.

Add understandable public-read and credential limits, failure responses, abuse safeguards, and regression coverage.

## Story 16.4 — Mature read/write resource contracts

**Status:** Planned.

Select a small set of mature capabilities for documented read/write access after scoped authentication and abuse controls are established.

## Story 16.5 — Webhooks and integration contract

**Status:** Planned.

Evaluate signed, retry-safe, idempotent webhook delivery for a bounded event set with privacy, replay, secret-rotation, delivery-failure, retention, and cost boundaries.

## Definition of done

Sprint 16 is complete when Ripple has a documented versioned API, scoped and revocable authentication for protected operations, rate/abuse controls, representative stable resource contracts, and an integration/webhook decision backed by privacy, operational, and regression evidence.
