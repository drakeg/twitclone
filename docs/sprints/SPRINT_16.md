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

**Status:** Completed in PR #229.

- Adds a dedicated `api_v1` Flask blueprint mounted at `/api/v1`.
- `GET /api/v1/` exposes API name, version, and read-only-preview status.
- `GET /api/v1/posts/<id>` exposes one globally public post through a bounded JSON contract.
- Removed, future-scheduled, and Ripple Space-scoped posts fail closed as `post_not_found`.
- The endpoint is read-only and exposes no email, admin, entitlement, moderation, or ORM-internal state.
- No token, API key, OAuth, write endpoint, webhook, paid service, or infrastructure activation is introduced.

## Story 16.2 — Scoped API authentication and revocation

**Status:** In implementation.

### Current implementation slice

- Adds a dedicated `ApiCredential` companion model rather than modifying the mature `User` model.
- Migration `20260913_0037_api_credentials.py` advances from migration `0036`.
- Raw bearer credentials use an `rpl_` prefix and are disclosed only at creation time.
- Ripple persists only a SHA-256 token digest plus a short non-secret display prefix.
- The initial supported scope is `posts:read`; unsupported scopes fail closed at issuance.
- Credentials expire after 90 days by default and may not exceed 365 days.
- Revocation is independent from browser sessions and account passwords.
- Successful bearer authentication records `last_used_at` for auditability.
- `GET /api/v1/account` exercises the protected bearer contract and requires `posts:read`.
- Browser login alone does not authenticate the protected API route.
- Operator CLI commands create, list, and revoke credentials without redisplaying stored bearer secrets.
- `docs/API_AUTHENTICATION.md` documents lifecycle, failures, rotation, secret handling, and product boundaries.

### Acceptance criteria

- Raw bearer tokens are never persisted in the database.
- A valid active credential with the required scope authenticates successfully.
- Missing, malformed, expired, revoked, and unknown tokens return a bounded `401 invalid_token` response.
- A valid credential lacking a required scope returns `403 insufficient_scope`.
- Browser session authentication cannot substitute for bearer authentication on protected API operations.
- Credential metadata includes creation, expiration, revocation, and last-use audit state.
- Credential expiration is bounded to a maximum of 365 days.
- Operators can create/list/revoke credentials without exposing stored secrets.
- API credentials do not alter ranking, reputation, verification, moderation authority, safety behavior, or paid reach.
- Tests cover hashing, scope validation, lifetime policy, browser-session isolation, bearer success, audit timestamp, revocation, and expiration.

### Story boundary

Story 16.2 does not add broad write access, OAuth, external identity-provider integration, refresh tokens, public self-service token issuance, webhooks, or rate-limit policy. Rate limiting and abuse controls remain Story 16.3 and must precede broad write capability.

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
