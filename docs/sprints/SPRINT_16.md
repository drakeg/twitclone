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

**Status:** Completed in PR #230.

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
- Operator CLI commands create, list, and revoke credentials without redisplaying raw secrets.
- `docs/API_AUTHENTICATION.md` documents lifecycle, failures, rotation, secret handling, and product boundaries.
- Broad writes, OAuth, public self-service issuance, webhooks, and rate-limit policy were deliberately deferred.

## Story 16.3 — Rate limiting and abuse boundaries

**Status:** In implementation.

### Current implementation slice

- Migration `20260913_0038_api_rate_limits.py` adds database-backed fixed-window counters shared across application processes.
- Public API reads default to 60 requests per client per 60-second window.
- Malformed, missing, expired, revoked, or unknown bearer attempts share a tighter 20-attempt client budget.
- Valid credentials default to 120 protected requests per credential per window.
- Public/invalid-token subjects are HMAC-SHA-256 hashed with the application secret before persistence; raw client addresses are not stored in rate-limit buckets.
- Valid credential limits use the internal credential ID and never persist or derive a limiter key from the raw bearer token.
- `429 rate_limited` responses include `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- Successful/ordinary limited responses expose the same limit/remaining/reset headers so clients can back off before a failure.
- Expired fixed-window buckets are opportunistically removed when new buckets are created.
- Configuration allows deployment-level adjustment through explicit `API_*` limit settings without changing the public failure contract.
- `docs/API_RATE_LIMITING.md` documents privacy, multi-process behavior, operational cost, DDoS boundaries, and product-integrity restrictions.

### Acceptance criteria

- Limits are shared through durable application storage rather than process-local memory.
- The current public-read surface returns a bounded 429 after its configured allowance is consumed.
- Invalid-token probing is bounded independently from normal valid-credential use.
- One valid credential does not consume another credential's allowance.
- Rate-limit persistence never stores raw client IP addresses or raw bearer secrets.
- Rate-limited responses provide a deterministic API error code and retry metadata.
- Fixed windows reset predictably after expiration.
- Existing visibility, authentication, revocation, and scope rules remain intact.
- Rate-limit state cannot affect ranking, reputation, verification, moderation authority, report priority, paid reach, or safety behavior.
- Tests cover public limits, invalid-token limits, valid credential limits, independent credential budgets, raw-identifier privacy, response headers, and window reset behavior.

### Story boundary

Story 16.3 is application-level abuse protection for the current low-volume API. It does not replace reverse-proxy/network DDoS protection and does not authorize a paid limiter service, Redis deployment, AWS resource, broad write access, OAuth, self-service credential issuance, or webhook delivery. Higher-volume infrastructure requires a separate operational and cost review.

## Story 16.4 — Mature read/write resource contracts

**Status:** Planned.

Select a small set of mature capabilities for documented read/write access after scoped authentication and abuse controls are established.

## Story 16.5 — Webhooks and integration contract

**Status:** Planned.

Evaluate signed, retry-safe, idempotent webhook delivery for a bounded event set with privacy, replay, secret-rotation, delivery-failure, retention, and cost boundaries.

## Definition of done

Sprint 16 is complete when Ripple has a documented versioned API, scoped and revocable authentication for protected operations, rate/abuse controls, representative stable resource contracts, and an integration/webhook decision backed by privacy, operational, and regression evidence.
