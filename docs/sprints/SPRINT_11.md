# Sprint 11 — Collaborative Knowledge and Resource Posts

**Status:** In implementation.

## Goal

Give Ripple a durable knowledge layer for guides, checklists, references, and community-maintained resources that should outlive an ordinary timeline post.

## Product hypothesis

Some useful contributions should be improved over time instead of repeatedly reposted into a feed. A resource should preserve attribution, revisions, supporting sources, and topic context so readers can understand both the current guidance and how it evolved.

## Guardrails

- Resource posts are distinct from ordinary timeline posts.
- Revision history is append-only; edits must not silently erase prior contributions.
- Each revision records the contributing account and time.
- Supporting sources remain visible when supplied.
- Topics reuse Ripple's explicit normalized topic vocabulary.
- Contributor or reviewer permissions are not purchased through a subscription or popularity metric.
- Sprint 11 does not create communities or topic-space membership; that remains Sprint 13 work.
- No feed ranking changes, AWS activation, or paid service are introduced by this sprint.

## Story 11.1 — Durable resource foundation

**Status:** Completed.

- A dedicated `/resources/` library stores durable resources separately from ordinary posts.
- Authenticated users can publish a title, body, optional HTTP/HTTPS supporting source, and up to five normalized explicit topics.
- Publication creates immutable revision 1 with author attribution.
- The resource points to its current revision while preserving historical revisions.
- Removed resources are excluded from public listing/detail.
- Migration `20260828_0024_resource_foundation.py` and focused regression coverage merged in PR #188.

## Story 11.2 — Attributable collaborative revisions

**Status:** In implementation.

**Goal:** Allow controlled improvements to a resource while preserving every prior version and the identity of each editor.

### Current implementation slice

- Resource owners can publish a new revision from resource detail.
- Administrators can publish a corrective revision when moderation/maintenance requires it; the administrator is recorded as the editor rather than impersonating the owner.
- Other authenticated users receive `403`; broad community editing is not enabled before a review/proposal model exists.
- Publishing appends the next revision number and moves `current_revision_id` to that revision.
- Earlier revisions remain unchanged and continue to display their original editor attribution.
- Every revision requires a concise change note and may provide a replacement supporting HTTP/HTTPS source.
- Removed resources cannot receive new revisions.
- The resource page exposes revision publication only to currently authorized accounts.
- No schema migration is required because Story 11.1 established the revision model.

### Acceptance criteria

- A revision never overwrites or deletes prior revision content.
- Current content advances only after a valid new revision is persisted.
- Editor attribution reflects the account that actually published the revision.
- Owners and administrators have explicit publication authority; unrelated users do not.
- A change note is required and retained with history.
- Source URL validation is applied consistently to revisions.
- Removed resources cannot be revised.
- Tests cover owner publication, authorization, administrator attribution, validation, history preservation, and removed-resource behavior.

### Permission decision

Story 11.2 deliberately uses a conservative publication boundary: owner or administrator. Topic reputation, follower count, verification, and paid membership do not grant edit authority. A broader community contribution workflow requires an explicit proposal/review path rather than direct write access and can be layered onto the append-only revision model in a later Story 11 slice.

## Story 11.3 — Revision review and comparison

**Status:** Planned.

- Make previous revisions inspectable.
- Provide an understandable current-vs-previous comparison or change summary.
- Preserve rejected/superseded history without presenting it as current guidance.

## Story 11.4 — Resource discovery

**Status:** Planned.

- Connect resource discovery to explicit topics and relevant conversations.
- Avoid turning resource discovery into paid placement or follower-count ranking.
- Provide useful empty/low-data states.

## Story 11.5 — Resource integrity and lifecycle

**Status:** Planned.

- Define moderation/removal behavior for resources and historical revisions.
- Keep source and attribution history understandable after corrections.
- Document ownership, contributor permissions, and future community integration boundaries.

## Definition of done

Sprint 11 is complete when Ripple supports durable, topic-associated resources that can be revised collaboratively with attribution and visible history, discovered without pay-to-win placement, and moderated without silently erasing provenance.
