# Sprint 33 — Space announcements and operator communication

**Status:** In progress.

## Goal

Give Space operators a durable member-communication surface that reduces manual
out-of-band coordination without turning announcements into global-feed reach,
ranking authority, or paid distribution.

## Story 33.1 — Persistent member-only announcements

**Status:** Implemented; validation in progress.

Add persistent announcements authored by Space owners/moderators and visible to
current Space members.

### Acceptance criteria

- Owners and moderators can publish announcements; regular members cannot.
- Announcements require a title of 1–120 characters and body of 1–1000
  characters.
- Current members can read announcements; public nonmembers cannot.
- Private-Space visibility continues to use the existing Space access boundary.
- New announcements cannot be published while a Space is archived, but existing
  announcements remain readable to authorized members.
- Announcements are ordered newest-first with deterministic tie-breaking and the
  detail page reads a bounded recent set.
- Author deletion may not delete the announcement; the author reference is
  nullable for future account deletion.
- Publishing an announcement does not create global-feed content, notification
  fanout, ranking/reputation changes, verification changes, or paid reach.
- The database change is represented by a reversible Alembic migration.

## Story 33.2 — Announcement lifecycle and audit

**Status:** Implemented; validation in progress.

Add operator-controlled edit, withdraw, and restore behavior with attributable
audit history so corrections are possible without silently rewriting or
deleting member communication.

### Acceptance criteria

- Owners/moderators can edit active announcements within Story 33.1 bounds.
- Edits preserve previous/new title and body in an attributable audit record.
- Withdraw is non-destructive: regular members no longer see the announcement,
  while operators retain visibility and can restore it.
- Restore makes the same announcement visible to members again without creating
  a replacement record.
- Archived Spaces block edit/withdraw/restore writes.
- Announcement audit history is operator-only, newest-first, and bounded.
- Actor deletion may null attribution without deleting audit history.
- Lifecycle actions do not fan out notifications or affect global feeds,
  ranking, reputation, verification, or paid status.
- Schema changes use a reversible Alembic migration.

## Story 33.3 — Member read state and sprint hardening

**Status:** Ready after Story 33.2 validation.

Add a lightweight read/unread member experience and close the sprint with
authorization, archive, deletion, ordering, migration, and no-ranking/no-paid-
reach regression coverage. Do not add email/push delivery or unbounded
per-member fanout without a separate design/cost decision.

## Boundary

Space announcements are local member communication. They do not purchase or
change organic reach, reputation, moderation authority, identity verification,
or global-feed placement.
