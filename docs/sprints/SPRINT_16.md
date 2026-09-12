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

### Current implementation slice

- Adds a dedicated `api_v1` Flask blueprint mounted at `/api/v1`.
- `GET /api/v1/` exposes only API name, version, and read-only-preview status.
- `GET /api/v1/posts/<id>` exposes one globally public post through a bounded JSON contract.
- The post contract includes only stable public fields: post ID/type/content, bounded author identity, publication timestamp, explicit public topic associations, and the corresponding public web path.
- Removed posts and future-scheduled posts return the same fail-closed `post_not_found` response.
- Tweets scoped to a Ripple Space are excluded from the global public-post endpoint, matching the global timeline boundary.
- The endpoint is read-only; unsupported write methods remain rejected.
- No token, API key, OAuth, write endpoint, webhook, third-party integration, new analytics event, migration, or infrastructure service is introduced.

### Acceptance criteria

- The API is namespaced under `/api/v1` so future incompatible contracts can be versioned independently.
- API responses do not expose passwords, email addresses, admin flags, entitlements, internal moderation fields, ORM relationship dumps, or other non-contract state.
- Removed, future-scheduled, and Space-scoped posts cannot be retrieved through the global post endpoint.
- A normal public post returns deterministic field names and a stable JSON envelope.
- Unsupported writes do not mutate posts.
- Automated tests cover version metadata, public-post serialization, visibility failures, Space isolation, and read-only behavior.
- No migration is required.

## Story 16.2 — Scoped API authentication and revocation

**Status:** Planned.

Define and implement a first-party API credential model with explicit scopes, secure token storage, revocation, expiration policy, auditability, and a migration path that does not reuse browser-session authentication as an API contract.

## Story 16.3 — Rate limiting and abuse boundaries

**Status:** Planned.

Add understandable per-credential and/or public-read limits, failure responses, operational safeguards, and tests before broadening the API surface.

## Story 16.4 — Mature read/write resource contracts

**Status:** Planned.

Select a small set of mature capabilities for documented read/write access after scoped authentication and abuse controls are established. Do not expose internal endpoints wholesale.

## Story 16.5 — Webhooks and integration contract

**Status:** Planned.

Evaluate signed, retry-safe, idempotent webhook delivery for a bounded event set. Document privacy, replay, secret rotation, delivery failure, retention, and operating-cost boundaries before activation.

## Definition of done

Sprint 16 is complete when Ripple has a documented versioned API, scoped and revocable authentication for any protected operations, rate/abuse controls, representative stable resource contracts, and an integration/webhook decision backed by privacy, operational, and regression evidence.
