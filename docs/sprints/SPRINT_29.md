# Sprint 29 — Space member operations

**Status:** Completed.

## Goal

Make day-to-day membership administration efficient for growing Ripple Spaces
without turning the member roster into a ranking surface or weakening existing
owner/moderator/privacy boundaries.

## Story 29.1 — Operator member roster

**Status:** Completed in PR #394.

Add a dedicated operator roster that scales beyond the existing 10-most-recent
summary.

### Acceptance criteria

- Only Space owners and moderators can access the operator roster.
- The roster supports case-insensitive username search.
- The roster supports role filtering for owner, moderator, and member.
- Results use deterministic ordering and bounded pagination.
- The page reports the filtered result count without presenting a quality,
  reputation, engagement, or popularity score.
- Owner/moderator/member roles remain authoritative from existing membership data.
- The roster does not expose email addresses or other non-public user data.
- Existing ownership transfer, role-change, removal, moderation, ranking,
  verification, and paid-status boundaries remain unchanged.

## Story 29.2 — Member-management workflow refinement

**Status:** Completed in PR #395.

Make the new roster operational for owners without broadening moderator authority:

- allow owners to change member/moderator roles from roster rows using existing audited role-change behavior;
- allow owners to remove non-owner members from roster rows using the existing explicit removal contract;
- preserve search, role filter, and page context after successful owner actions;
- keep moderators read-only and keep ownership transfer on the existing dedicated workflow.

### Acceptance criteria

- Moderator roster access remains read-only.
- Owners cannot change/remove the current owner from roster controls.
- Role changes and removals continue writing the existing membership-administration audit history.
- Successful roster actions redirect back to the same roster search/filter/page context.
- Detail-page member administration continues to work and still redirects to the Space detail page.
- No bulk removal or ownership-transfer shortcut is added.

## Story 29.3 — Sprint regression hardening

**Status:** Completed in PR #396.

Closed the sprint with edge-case regression coverage for invalid filters, empty
searches, lower/upper page bounds, filter-preserving pagination, archived-space
read access, and the existing authorization/audit boundaries.

## Boundary

Sprint 29 improves operator workflow; it does not introduce member ranking,
engagement scoring, private-data export, bulk removal, paid moderation authority,
or any mechanism that changes global reputation/reach.
