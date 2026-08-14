# ADR-0022: Notification read lifecycle

- Status: Accepted
- Date: 2026-08-13
- Sprint: 4
- Story: 4.2

## Context

Notifications have a `read` field, but the database allowed null values and the
application never changed the field. Consequently, there was no defined point
at which a notification transitioned from unread to read.

The existing product exposes a single notification inbox and no per-item detail
or dismissal actions. Adding controls or a navigation badge would combine the
lifecycle decision with a separate UI change.

## Decision

Use a simple inbox-based lifecycle:

- every new Notification starts unread;
- `read` is non-nullable and defaults to false in both the model and database;
- opening `/notifications` marks every unread Notification owned by the current
  user as read before rendering the inbox;
- notifications owned by other users are never read or changed; and
- repeated inbox visits are idempotent.

The migration converts legacy null values to false before enforcing the column
constraint.

## Consequences

- Notification state now has one predictable transition.
- Read state is enforced even for records inserted outside the ORM.
- The existing page, URL, ordering, and visual presentation remain unchanged.
- Opening the inbox acknowledges all visible and previously created
  notifications at once.

## Guardrails

- Notification queries and state changes must always be scoped to the
  authenticated owner.
- Future unread counts must derive from `read = false` without changing state.
- Per-notification read, dismissal, retention, or deletion behavior requires a
  separate product and authorization decision.
