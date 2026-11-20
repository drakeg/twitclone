# Sprint 26 — Space ownership and membership administration

**Status:** Completed.

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

**Status:** Completed in PR #384.

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

**Status:** Completed in PR #385.

- Add a dedicated durable membership-administration action model.
- Record ownership transfers, member removals, and owner-driven role changes.
- Preserve actor and affected-user attribution while allowing deleted accounts to resolve safely.
- Show the recent history to Space owners on the operator dashboard.
- Keep content moderation history separate from membership administration.

### Acceptance criteria

- Membership administration has its own table and migration.
- Role changes stop writing new records into the content-moderation audit.
- Ownership transfer records the target's previous role and new owner role.
- Member removal records the removed role and a null new role.
- Only the Space owner sees membership-administration history in the operator UI.
- Deleting a user does not require deleting historical administration records.

## Boundary

Sprint 26 improves Space administration only. It does not add private/invite-only
Spaces, paid membership gating, global account suspension, or enterprise
directory integration unless later stories explicitly select those capabilities.

## Sprint outcome

Sprint 26 delivered safe ownership transfer, owner-controlled membership removal,
and a dedicated membership-administration audit trail. Space communities can now
change hands and maintain a reviewable administrative history without conflating
membership operations with content moderation.

## Definition of done

Completed. Ownership handoff, member removal, and membership administration history
are implemented and regression-tested.
