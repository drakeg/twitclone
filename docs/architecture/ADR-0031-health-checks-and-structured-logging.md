# ADR-0031: Health checks and structured logging

- Status: Accepted
- Date: 2026-08-16
- Sprint: 6
- Story: 6.2

## Context

The container had no machine-readable health signal, and application and worker
messages used inconsistent plain text. Operators could not distinguish a live
process from one unable to reach its database or correlate a response with its
request log.

## Decision

- Add separate unauthenticated liveness and database-readiness endpoints.
- Make Compose probe readiness with Python's standard library.
- Emit one-line JSON application logs to standard error.
- Log request completion with a bounded correlation ID, method, path, status,
  and duration, while excluding sensitive request data.
- Use the same structured logger hierarchy for scheduled-worker events.
- Add no external observability dependency in this story.

## Consequences

- Compose and future platforms can distinguish process health from dependency
  readiness.
- Container log collectors can parse application events without multiline or
  format-specific rules.
- Database readiness adds one small query per probe interval.
- Metrics, tracing, alert routing, and external monitoring remain deployment
  concerns.

## Guardrails

- Health responses must not expose exception or configuration details.
- Liveness must not depend on the database or another external service.
- Logs must not contain secrets, cookies, authorization headers, request bodies,
  or query strings.
