# ADR-0028: Poll expiration behavior

- Status: Accepted
- Date: 2026-08-15
- Sprint: 5
- Story: 5.4

## Context

Polls exposed a calculated `is_active` property to templates, but the voting
endpoint did not enforce it. A crafted request could therefore vote after the
UI displayed results. Rendering also depended on a separate wall-clock read,
making exact-boundary behavior difficult to test consistently.

## Decision

- A poll expires at `created_at + duration`.
- Its active interval is half-open: it accepts votes only while `now < expires_at`.
- At the exact expiration timestamp and afterward, voting is rejected without
  changing vote records or counters.
- Timeline assembly computes activity from the same request timestamp used for
  the rest of the timeline and passes that decision to the template.
- Expired polls remain visible and display final results.

## Consequences

- Direct requests cannot bypass expiration.
- Server behavior and rendered controls use one rule.
- No schema migration or Compose change is required; `docker compose up --build`
  remains the documented local workflow.

## Guardrails

- Future timezone work must preserve the half-open boundary.
- Vote mutation must always re-check expiration on the server.
