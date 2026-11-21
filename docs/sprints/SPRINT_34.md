# Sprint 34 — Space events and meetups

**Status:** Closeout implementation in progress.

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

**Status:** Implemented; validation in progress.

Add non-destructive edit, cancel, and restore behavior with attributable audit
history.

### Acceptance criteria

- Owners/moderators can edit active events using the same bounded/timezone-safe
  validation as creation.
- Edits preserve previous/new title, description, location, UTC start, and
  timezone in audit history.
- Cancel is non-destructive: regular members no longer see the event, while
  operators retain visibility and may restore a future event.
- Past canceled events cannot be restored.
- Archived Spaces block edit/cancel/restore writes.
- Operator audit history is newest-first, attributable, and capped at 50.
- Actor deletion may null attribution without deleting event/audit history.
- Lifecycle actions do not create delivery fanout or change feeds, ranking,
  reputation, verification, or paid status.
- Schema changes use a reversible Alembic migration.

## Story 34.3 — RSVP and sprint hardening

**Status:** Implemented; validation in progress.

Add lightweight member RSVP state and close the sprint with regression
hardening.

### Acceptance criteria

- Current Space members can set Going or Maybe for an upcoming active event and
  clear/change their own RSVP; nonmembers cannot RSVP.
- RSVP state is unique per event/user and updates idempotently rather than
  creating duplicates.
- Member UI exposes aggregate Going/Maybe counts plus only the current member's
  own RSVP; it does not expose attendee identity lists.
- Event creation creates no per-member RSVP rows, notification fanout, or
  delivery jobs.
- Canceled, past, and archived-Space events reject RSVP writes.
- Event/user deletion cascades remove obsolete RSVP rows.
- Reversible migration, timezone/DST validation, authorization, lifecycle,
  ordering, archive, and no-ranking/no-paid-reach regressions remain covered.
- Email/push/calendar-provider delivery and ticketing remain out of scope.

## Boundary

Sprint 34 remains Space-local. Email/push/calendar-provider integration,
unbounded attendee fanout, ticket sales, and paid event promotion are out of
scope without separate product/cost decisions.
