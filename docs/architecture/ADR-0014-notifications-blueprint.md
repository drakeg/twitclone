# ADR-0014: Notifications Blueprint

- Status: Accepted
- Date: 2026-08-06
- Sprint: 2
- Story: 2.9

## Context

The notification inbox remains in `app.py` after the authentication, timeline,
messaging, and polls extractions. Notification records are created by several
existing workflows, but the inbox itself is a single cohesive read route.

Changing notification lifecycle, read state, generation, or retention would be
product work beyond this structural story.

## Decision

Create `twitclone.notifications` with a `notifications` Blueprint owning
`/notifications`.

Register the route from the application factory with its existing endpoint name.
Preserve the template, login protection, current-user filtering, descending
timestamp order, and read-only behavior.

Notification creation remains with the workflows that currently produce each
record. The old notification function in `app.py` is temporarily dormant
compatibility code and no longer owns a URL rule in the supported factory path.

## Consequences

### Positive

- The notification inbox now has package route ownership.
- Existing URL and template endpoint references remain stable.
- The route depends directly on the package-owned Notification model.
- Future notification lifecycle work has a clear route boundary.

### Negative

- Unqualified endpoint compatibility requires a Blueprint registration hook.
- Notification writes remain distributed across feature Blueprints.
- The dormant implementation remains until final monolith cleanup.

## Guardrails

- Read-state, retention, generation, and authorization changes require separate
  stories and focused tests.
- No templates, models, migrations, dependencies, or UI change in this story.
