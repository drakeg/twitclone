# ADR-0035: Preserve naive UTC storage while replacing deprecated clocks

- Status: Accepted
- Date: 2026-08-16

## Context

The existing database schema stores timestamps in timezone-naive SQLAlchemy
`DateTime` columns, while Python deprecates `datetime.utcnow()` in favor of
timezone-aware UTC clocks.

## Decision

Generate current UTC time with `datetime.now(UTC)` and remove the timezone
marker before values enter the existing naive timestamp contract. This removes
the deprecated API without mixing aware and naive datetime objects in current
queries, sorting, poll expiration checks, or scheduled-post comparisons.

## Consequences

- Existing database columns and migration history do not change.
- Current UTC semantics remain compatible with stored timestamps.
- A future migration to timezone-aware database columns should be handled as a
  separate schema change rather than being hidden inside this maintenance fix.
