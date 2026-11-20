# Sprint 26 — Space ownership and membership administration

**Status:** In progress.

## Goal

Make persistent Ripple Spaces operationally sustainable by giving owners safe,
explicit tools to hand off responsibility and manage membership without trapping
a community around its original creator.

## Story 26.1 — Safe ownership transfer

**Status:** Completed in PR #383.

- Allow the current owner to transfer ownership only to an existing Space member.
- Require an explicit confirmation before the transfer is committed.
- Atomically demote the previous owner to member, promote the selected member to
  owner, and update the Space's canonical owner.
- Notify the new owner.
- Preserve the former owner's ability to remain or use the existing leave flow.
- Reject non-owner attempts, missing confirmation, and self-transfer.

### Acceptance criteria

- A Space always has exactly one canonical owner after a successful transfer.
- The ownership membership role and `space.owner_id` stay consistent.
- Transfer targets must already belong to the Space.
- Moderators and members can both be selected as the next owner.
- The previous owner becomes a normal member and can leave afterward.
- No global ranking, verification, reputation, paid entitlement, or moderation
  authority outside that Space is changed.

## Planned follow-up stories

### Story 26.2 — Owner member removal

**Status:** In progress.

- Allow only the canonical Space owner to remove a non-owner membership.
- Require an explicit removal confirmation.
- Notify the affected user that their current membership ended.
- Explain that removal from a public Space is not a ban and the user may rejoin.
- Preserve the ownership-transfer requirement before an owner can be removed.

### Acceptance criteria

- Non-owners cannot remove Space memberships.
- The current owner cannot be removed through this workflow.
- A successful removal revokes the member or moderator role immediately.
- Removal does not delete the user's account, posts, resources, or global relationships.
- Because Sprint 26 does not add bans or private Spaces, removed users may rejoin a public Space.
- The UI communicates that boundary instead of implying a permanent ban.

### Story 26.3 — Membership administration audit

Add a durable, reviewable membership-administration history for ownership
transfer, member removal, and role changes without conflating those actions with
content moderation.

## Boundary

Sprint 26 improves Space administration only. It does not add private/invite-only
Spaces, paid membership gating, global account suspension, or enterprise
directory integration unless later stories explicitly select those capabilities.
