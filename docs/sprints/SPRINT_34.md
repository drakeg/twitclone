# Sprint 34 — Space events and meetups

**Status:** In progress.

## Goal

Give Space operators a durable, timezone-safe way to schedule member meetups
without introducing global-feed promotion, paid reach, or external calendar
infrastructure.

## Story 34.1 — Timezone-safe upcoming events

**Status:** Implemented; validation in progress.

Add persistent upcoming events created by Space owners/moderators and visible to
current Space members.

### Acceptance criteria

- Owners/moderators can schedule events; regular members cannot.
- Events require a title of 1–120 characters and description of 1–1000
  characters; location is optional and capped at 200 characters.
- Operators enter a local start plus explicit IANA timezone; Ripple stores UTC.
- Invalid IANA zones and ambiguous/nonexistent DST local times are rejected
  rather than silently converted.
- Events must be in the future when created.
- Current members can view upcoming events; public nonmembers cannot.
- Archived Spaces keep previously scheduled events readable to members but block
  new event creation.
- Upcoming display is chronological, deterministic, and capped at 20 records.
- Event creator attribution can become null if an account is deleted without
  deleting the event.
- Schema is represented by a reversible Alembic migration.
- Events do not affect feeds, ranking, reputation, verification, or paid status.

## Story 34.2 — Event lifecycle

**Status:** Planned.

Add edit/cancel behavior with attributable audit history so schedules can change
without silently rewriting member communication.

## Story 34.3 — RSVP and sprint hardening

**Status:** Planned.

Add lightweight member RSVP state without event-time fanout, then close the
sprint with timezone, authorization, archive, lifecycle, migration, and
no-ranking/no-paid-reach regressions.

## Boundary

Sprint 34 remains Space-local. Email/push/calendar-provider integration,
unbounded attendee fanout, ticket sales, and paid event promotion are out of
scope without separate product/cost decisions.
