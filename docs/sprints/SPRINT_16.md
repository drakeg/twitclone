# Sprint 16 — Public API and Integrations

**Status:** In implementation.

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

- Adds a dedicated `api_v1` Flask blueprint mounted at `/api/v1`.
- `GET /api/v1/` exposes API name and version.
- `GET /api/v1/posts/<id>` exposes one globally public post through a bounded JSON contract.
- Removed, future-scheduled, and Ripple Space-scoped posts fail closed as `post_not_found`.
- The endpoint exposes no email, admin, entitlement, moderation, or ORM-internal state.

## Story 16.2 — Scoped API authentication and revocation

**Status:** Completed in PR #230.

- Adds dedicated `ApiCredential` persistence with one-time raw bearer disclosure and hashed-at-rest tokens.
- Credentials expire, revoke independently, and record successful use.
- `GET /api/v1/account` requires explicit `posts:read` scope.
- Browser session cookies do not authenticate protected API operations.
- Operator CLI commands create, list, and revoke credentials without redisplaying raw secrets.
- `docs/API_AUTHENTICATION.md` records lifecycle and secret-handling boundaries.

## Story 16.3 — Rate limiting and abuse boundaries

**Status:** Completed in PR #231.

- Migration `20260913_0038_api_rate_limits.py` adds database-backed fixed-window counters shared across application processes.
- Public reads default to 60 requests per client per 60-second window.
- Invalid bearer probing uses a tighter 20-attempt client budget.
- Valid credentials default to 120 protected requests per credential per window.
- Public/invalid-token subjects are HMAC-SHA-256 hashed before persistence; raw client addresses are not stored.
- Valid credential limits use the internal credential ID rather than raw bearer material.
- Rate-limit responses expose deterministic headers and bounded `429 rate_limited` failures.
- `docs/API_RATE_LIMITING.md` documents privacy, operational, abuse, and cost boundaries.

## Story 16.4 — Mature read/write resource contracts

**Status:** In implementation.

### Current implementation slice

- Existing `GET /api/v1/posts/<id>` remains the stable public read contract for globally visible posts.
- Adds the explicit `posts:write` bearer scope; `posts:read` remains separate.
- Adds `POST /api/v1/posts` as the first bounded write contract.
- The write contract accepts required text content, optional conversation intent, and up to five explicit topic strings.
- Post text reuses Ripple's existing 144-character validation.
- Conversation intent reuses Ripple's existing intentional-conversation normalization.
- Explicit topics reuse Ripple's existing normalized topic association logic.
- API-created posts participate in ordinary mention notifications and public moderation/reporting behavior.
- Successful creates return `201 Created`, the same bounded public post representation used by reads, and a stable `Location` header.
- Read-only credentials fail closed with `403 insufficient_scope` on the write endpoint.
- Existing credential rate limits apply to write operations.
- The API index advertises the bounded `posts:read` and `posts:write` scope set and changes status from read-only preview to limited-write preview.
- `docs/API_RESOURCE_CONTRACTS.md` documents the v1 contract and deliberate exclusions.
- No migration is required for the new scope because credential scopes are already stored as an explicit bounded string set.

### Acceptance criteria

- A credential with `posts:write` can create one ordinary globally public text post.
- A `posts:read`-only credential cannot create posts.
- Invalid/non-JSON/blank/oversized payloads fail closed without creating a post.
- More than five topic values or non-string topic entries are rejected.
- Created posts are immediately readable through the existing public post endpoint when otherwise visible.
- API responses do not serialize private ORM fields.
- Write access does not confer ranking, reputation, verification, moderation, entitlement, or paid-reach effects.
- Tests cover supported scope issuance, scope isolation, valid creation, public read-back, validation failures, and API capability advertisement.

### Story boundary

Story 16.4 intentionally excludes API media upload, scheduling, deletion, editing, replies, reposts, polls, Space posting, moderation, billing, verification, credential self-service, OAuth, and admin operations. Those workflows require separately specified contracts rather than accidental exposure.

## Story 16.5 — Webhooks and integration contract

**Status:** Planned.

Evaluate signed, retry-safe, idempotent webhook delivery for a bounded event set with privacy, replay, secret-rotation, delivery-failure, retention, and cost boundaries.

## Definition of done

Sprint 16 is complete when Ripple has a documented versioned API, scoped and revocable authentication for protected operations, rate/abuse controls, representative stable resource contracts, and an integration/webhook decision backed by privacy, operational, and regression evidence.
