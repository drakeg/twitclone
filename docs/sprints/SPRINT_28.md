# Sprint 28 — Space settings and lifecycle

**Status:** In progress.

## Goal

Make Ripple Spaces maintainable after creation by giving owners safe settings and
lifecycle controls without breaking stable URLs or silently deleting community data.

## Story 28.1 — Owner Space settings

**Status:** In progress.

- Add owner-only editing for Space name, description, and visibility.
- Preserve the Space slug/URL during settings changes.
- Preserve all memberships, posts, resources, invitations, and audit history.
- Apply public/private access changes immediately after save.

### Acceptance criteria

- Only the canonical owner can access or submit Space settings.
- Name and description retain the same validation bounds as creation.
- Visibility is limited to public/private.
- The slug is not editable and remains unchanged.
- Switching private to public restores normal discovery/self-join.
- Switching public to private immediately hides the Space from nonmembers while retaining members.

## Planned follow-up stories

### Story 28.2 — Space archive state

Allow owners to archive a Space without deleting history. Archived Spaces become
read-only and stop accepting new posts, resources, invitations, and memberships.

### Story 28.3 — Archive restore and lifecycle audit

Allow owner restoration of archived Spaces and record settings/archive lifecycle
changes in a durable owner-visible administrative history.

## Boundary

Sprint 28 favors reversible lifecycle controls. Permanent destructive Space deletion
is not included unless a later sprint explicitly defines retention/export safeguards.
