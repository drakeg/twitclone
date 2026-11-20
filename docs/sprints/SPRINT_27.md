# Sprint 27 — Space invitations and access control

**Status:** In progress.

## Goal

Give Ripple Spaces explicit, consent-based membership onboarding and build the
foundation for private/invite-controlled communities without silently adding users.

## Story 27.1 — Consent-based Space invitations

**Status:** In progress.

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

Allow operators to review and cancel pending invitations and make invitation
state visible from the operator dashboard.

### Story 27.3 — Private Space visibility

Use the invitation/membership contract to introduce private Spaces with explicit
access boundaries while keeping public Spaces unchanged.

## Boundary

Sprint 27 does not add email invitations to non-users, enterprise directory sync,
paid membership gating, or global account access control.
