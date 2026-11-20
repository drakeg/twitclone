# Sprint 27 — Space invitations and access control

**Status:** Completed.

## Goal

Give Ripple Spaces explicit, consent-based membership onboarding and build the
foundation for private/invite-controlled communities without silently adding users.

## Story 27.1 — Consent-based Space invitations

**Status:** Completed in PR #386.

- Allow Space owners and moderators to invite an existing Ripple user by username.
- Never create membership at invite time.
- Notify the invited user and provide a dedicated pending-invitations view.
- Allow only the invited user to accept or decline.
- Create a normal member role only after acceptance.
- Prevent duplicate pending invitations and invitations to existing members.

### Acceptance criteria

- Owners/moderators can invite; ordinary members cannot.
- Invitations target existing Ripple accounts only.
- Pending invitations are visible only to the invited user.
- Acceptance creates at most one Space membership.
- Decline does not create membership.
- Duplicate pending invites do not create duplicate records.
- Invitations do not affect global ranking, reputation, verification, or paid status.

## Planned follow-up stories

### Story 27.2 — Invitation management

**Status:** In progress.

- Show pending invitations and a count on the operator dashboard.
- Allow owners and moderators to cancel a pending invitation.
- Notify the invited user when an outstanding invitation is canceled.
- Prevent canceled invitations from being accepted afterward.

### Acceptance criteria

- Operator dashboard lists only pending invitations for that Space.
- Owners and moderators can cancel pending invitations; ordinary members cannot.
- Canceling records `canceled` status and a response timestamp.
- Canceled invitations cannot be accepted or declined later.
- Cancellation does not create or remove Space membership.

### Story 27.3 — Private Space visibility

Use the invitation/membership contract to introduce private Spaces with explicit
access boundaries while keeping public Spaces unchanged.

## Boundary

Sprint 27 does not add email invitations to non-users, enterprise directory sync,
paid membership gating, or global account access control.

## Sprint outcome

Sprint 27 delivered consent-based existing-user invitations, operator invitation
management, and private Space visibility/access controls while preserving public
Space behavior.

## Definition of done

Completed. Invitations require recipient consent, operators can manage pending
invitations, and private Spaces are discoverable/viewable only by members.
