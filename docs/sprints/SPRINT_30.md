# Sprint 30 — Space conversation curation

**Status:** In progress.

## Goal

Give Space operators lightweight curation controls that keep important
community conversations visible without changing global feed ranking,
reputation, verification, or paid reach.

## Story 30.1 — Pin and unpin Space conversations

**Status:** In progress.

Allow Space owners and moderators to pin an existing visible Space post and
later unpin it.

### Acceptance criteria

- Only Space owners and moderators can pin or unpin a Space post.
- Pinning changes only ordering inside that Space.
- The underlying Tweet remains unchanged and keeps its normal global behavior.
- Hidden/removed Space posts cannot be pinned.
- Pinned posts appear before unpinned posts; each group remains deterministic.
- The UI clearly labels pinned conversations and exposes pin/unpin controls only
  to operators.
- Archive state remains readable; pin/unpin mutations are paused while archived.
- Pin/unpin actions are auditable without mixing them into membership history.
- Payment, verification, follower count, reputation, and global engagement do
  not influence pin state.

## Story 30.2 — Curated-conversation usability refinement

**Status:** Planned after Story 30.1 is exercised.

Use concrete implementation/test gaps to improve curation usability without
adding algorithmic ranking or bulk moderation.

## Story 30.3 — Sprint regression hardening

**Status:** Planned.

Close the sprint with authorization, lifecycle, moderation, ordering, and
migration regression coverage.

## Boundary

Sprint 30 is Space-local operator curation. It does not sell reach, modify
global feed ordering, change topic reputation, bypass moderation, or create a
general-purpose recommendation algorithm.
