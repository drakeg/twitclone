# Sprint 31 — Private Space membership requests

**Status:** In progress.

## Goal

Let people express interest in joining private Spaces without weakening operator
control, privacy, invitation consent, or Ripple-wide safety boundaries.

## Story 31.1 — Request private Space membership

**Status:** Completed in PR #400.

Add a requester-initiated workflow that creates a pending membership request for
a private Space and lets owners/moderators explicitly approve or deny it.

### Acceptance criteria

- Only authenticated nonmembers may create a membership request.
- Requests are available only for private Spaces; public Spaces keep normal
  self-join behavior.
- A user can have at most one pending request per Space.
- Existing members and users with an already-pending request cannot create
  duplicates.
- Requesters may include a bounded optional note visible only to Space operators.
- Owners/moderators can review pending requests.
- Approval creates membership exactly once and resolves the request.
- Denial resolves the request without creating membership.
- Operator decisions record actor/time and remain auditable if an actor account
  is later deleted.
- Archived Spaces reject new requests and approval/denial mutations.
- Private Space content remains hidden from nonmembers while a request is
  pending; the request flow must not become a content-discovery bypass.
- Membership requests do not affect global ranking, reputation, verification,
  or paid status.

## Story 31.2 — Operator request-link and notification usability

**Status:** In progress.

Make the request workflow discoverable for operators without making private
Spaces publicly discoverable.

### Acceptance criteria

- Private-Space operator dashboards expose a stable request-access URL that can
  be shared intentionally.
- Public Space operator dashboards do not show a request-access URL.
- The request link itself still exposes no private Space content to nonmembers.
- New membership requests notify all current owners/moderators, not unrelated
  members/users.
- Notification changes do not create membership or auto-approval behavior.
- Existing privacy, archive, and request-resolution boundaries remain unchanged.

## Story 31.3 — Sprint regression hardening

**Status:** Planned.

Close the sprint with duplicate, authorization, privacy, lifecycle, audit, and
invitation-interaction regression coverage.

## Boundary

Sprint 31 adds explicit request/review mechanics only. It does not automatically
approve membership, expose private Space content to requesters, sell access, or
change global social/reputation systems.
