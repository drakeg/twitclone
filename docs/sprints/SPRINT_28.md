# Sprint 28 — Space settings and lifecycle

**Status:** In progress.

## Goal

Make Ripple Spaces maintainable after creation by giving owners safe settings and
lifecycle controls without breaking stable URLs or silently deleting community data.

## Story 28.1 — Owner Space settings

**Status:** Completed in PR #389.

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

**Status:** Completed in PR #390.

- Allow only the canonical owner to archive a Space with explicit confirmation.
- Preserve all memberships, posts, resources, invitations, moderation, and audit history.
- Keep archived Spaces viewable under their existing public/private visibility rules.
- Block new memberships, accepted invitations, posts, resource links, and new invitations.
- Keep moderation and existing-member leave available.

### Acceptance criteria

- Archiving never deletes Space data.
- Archived state records when and by whom the action occurred.
- Non-owners cannot archive.
- Archived Spaces reject join, invitation acceptance, new invitation, posting, and resource-link creation.
- Existing content/history remains readable to anyone who could already view the Space.
- Existing members may leave and operators may continue moderation.
- Settings mutations are paused until the Space is restored.

### Story 28.3 — Archive restore and lifecycle audit

**Status:** In progress.

- Allow only the canonical owner to restore an archived Space with explicit confirmation.
- Resume participation under the Space's existing visibility settings.
- Add a dedicated lifecycle audit model for settings updates, archive, and restore.
- Show lifecycle history only to the Space owner on the operator dashboard.
- Preserve lifecycle history when actor accounts are later deleted.

### Acceptance criteria

- Restore clears archive state without changing slug, visibility, membership, or content.
- Non-owners cannot restore.
- Restored public Spaces resume discovery/self-join; restored private Spaces resume invitation-based membership.
- Settings changes record previous/new name and visibility plus whether description changed.
- Archive and restore actions record actor/time and lifecycle state.
- Lifecycle audit remains separate from moderation and membership-administration histories.

## Boundary

Sprint 28 favors reversible lifecycle controls. Permanent destructive Space deletion
is not included unless a later sprint explicitly defines retention/export safeguards.
