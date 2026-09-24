# Legacy TODO Status

This file used to act as the project's informal backlog. It is retained only as
historical context.

The authoritative product roadmap is now:

- `docs/ROADMAP.md`
- active/completed sprint records under `docs/sprints/`
- accepted architectural decisions under `docs/architecture/`

Do not add new work to this file. New product work should be added to the
numbered roadmap or the active sprint document so Ripple has one backlog source
of truth.

## Reconciled items

The following items from the original TODO are already delivered and should no
longer be treated as pending work:

- user profile pages and profile customization;
- clickable mentions/hashtags and topic discovery;
- search/discovery across people and topics;
- visible post timestamps;
- server-side validation and authorization coverage;
- PostgreSQL production support and migration tooling;
- CI validation and production deployment contracts;
- password/account recovery;
- notifications for social activity and messages;
- responsive UI refresh and accessibility hardening.

## Still deferred or conditional

These ideas were present in the legacy TODO but are **not** current roadmap
commitments unless separately promoted into a numbered sprint:

- social-login providers such as Google/Facebook;
- real-time push/WebSocket notifications;
- actual AWS production activation and recurring infrastructure spend;
- usage-driven UX refinements that require real-user evidence.

AWS activation remains explicitly separate from roadmap inclusion and requires
specific authorization before any paid resources are provisioned.

## Current development

As of Sprint 21, active work is tracked in
`docs/sprints/SPRINT_21.md`. The sprint covers author-controlled post lifecycle
behavior, including owner-only editing and soft removal of original posts.

## Historical note

The original TODO predates Ripple's numbered sprint process and contains several
descriptions using the old "Twitter Clone" terminology. Those descriptions are
not current product specifications and should not override newer sprint or ADR
decisions.
