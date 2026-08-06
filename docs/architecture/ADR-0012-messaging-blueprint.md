# ADR-0012: Messaging Blueprint

- Status: Accepted
- Date: 2026-08-05
- Sprint: 2
- Story: 2.7

## Context

The direct-message inbox and reply routes remain in `app.py` after the
authentication and timeline extractions. They form a small route group with
clear model dependencies and existing templates.

The timeline `/tweet` route also accepts a legacy `/dm` command. Moving or
redesigning that command would cross the established Timeline Blueprint boundary
and change more than this structural story requires.

## Decision

Create `twitclone.messaging` with a `messaging` Blueprint owning:

- `/messages`
- `/reply/<message_id>`

Register both routes from the application factory with their existing endpoint
names. Preserve inbox ordering, templates, login protection, reply length
handling, notification creation, flash messages, redirects, and current
authorization behavior.

The `/tweet`-based `/dm` compatibility path remains in the Timeline Blueprint.
The old messaging functions in `app.py` are temporarily dormant compatibility
code and no longer own URL rules in the supported factory path.

## Consequences

### Positive

- Inbox and reply behavior now has package ownership.
- Existing URLs and template endpoint references remain stable.
- Messaging routes depend directly on package-owned extensions and models.
- Notification route ownership remains available for its planned later story.

### Negative

- Unqualified endpoint compatibility requires a Blueprint registration hook.
- Dormant implementations remain until final monolith cleanup.
- Existing reply authorization behavior is preserved even though it warrants a
  separate security review.
- Message creation remains split between Timeline and Messaging temporarily.

## Guardrails

- Authorization or validation changes require separate stories and tests.
- No templates, models, migrations, dependencies, or UI change in this story.
- The `/dm` command moves only through a coordinated Timeline and Messaging
  change.
