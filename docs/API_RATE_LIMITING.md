# Ripple API rate limiting and abuse boundaries

Sprint 16 Story 16.3 establishes bounded, understandable limits for the current `/api/v1` surface before Ripple authorizes broader write access.

## Current limits

The default fixed window is 60 seconds.

- Public read requests: **60 requests per client per window**.
- Invalid or malformed bearer attempts: **20 attempts per client per window**.
- Valid API credentials: **120 protected requests per credential per window**.

The application configuration keys are `API_RATE_LIMIT_WINDOW_SECONDS`, `API_PUBLIC_READ_LIMIT`, `API_INVALID_TOKEN_LIMIT`, and `API_CREDENTIAL_LIMIT`. Deployment-specific changes should be reviewed as operational policy changes rather than silently altered in application code.

## Identity and privacy boundary

Public and invalid-token limits use the request's client address only as a short-lived rate-limit identifier. Ripple does not persist the raw address in rate-limit storage. The identifier is HMAC-SHA-256 hashed with the application secret before persistence.

Valid credential requests are keyed by Ripple's internal credential ID, never by the raw bearer secret or stored token digest.

Rate-limit buckets contain only a bucket type, hashed/opaque subject identifier, fixed-window timestamps, and request count. Expired buckets are opportunistically deleted when a new bucket is created.

## Response contract

Rate-limited requests return HTTP `429` with the bounded API error code `rate_limited`.

Responses subject to a limit include:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

A blocked response additionally includes `Retry-After`.

The API does not reveal whether an invalid bearer token ever existed, who owned it, or why it failed authentication.

## Abuse-control boundaries

The invalid-token budget is deliberately tighter than ordinary authenticated use to reduce brute-force and credential-probing volume. A valid credential receives an independent budget, so one credential does not consume another credential's allowance.

Current limits are database-backed so they are shared across multiple application processes. This avoids process-local counters that can be bypassed by requests landing on different workers. The tradeoff is one small database write per limited request. Before materially increasing API traffic, Ripple should review storage/write load and may move the same contract to a dedicated shared limiter such as Redis only after an operational/cost review.

These controls do not replace network-level DDoS protection, reverse-proxy limits, provider abuse controls, or incident response. They are application-level safeguards for the current low-volume API contract.

## Product integrity

Rate limiting is not a ranking, reputation, verification, moderation, or monetization signal. Rate-limit state must not influence feed ordering, topic/community contribution context, verification approval, report priority, paid reach, or safety decisions.

No user behavioral profile, emotional state, ideology, sensitive interest, or precise-location history is created by this feature.

## Story boundary

Story 16.3 does not authorize broad public write access, OAuth, self-service API credential issuance, webhook delivery, a paid API tier, AWS activation, or new recurring infrastructure spend. Story 16.4 must select and document any mature write contracts separately.
