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

**Status:** Completed.

- Resource owners and administrators can publish append-only revisions.
- The account that publishes a revision is always recorded as its editor.
- Unrelated users cannot directly edit a resource.
- Every revision requires a retained change note and receives consistent source URL validation.
- Removed resources cannot receive new revisions.
- No reputation, follower, verification, or paid entitlement grants edit authority.
- Story 11.2 merged in PR #189.

## Story 11.3 — Revision review and comparison

**Status:** In implementation.

**Goal:** Let readers inspect exactly what any historical revision said and understand what changed without confusing superseded guidance with the current resource.

### Current implementation slice

- Every revision in resource history links to a stable inspection route: `/resources/<resource_id>/revisions/<revision_number>`.
- Revision pages show the exact historical body, editor, timestamp, change note, and source that belonged to that revision.
- Current and historical revisions are labeled explicitly.
- Each revision after revision 1 includes a deterministic line-level comparison against its immediately preceding revision.
- Added and removed lines are labeled in plain language rather than silently replacing historical content.
- Revision 1 clearly states that no earlier comparison exists.
- Previous/next revision navigation makes the history browsable.
- Unknown revision numbers and revisions belonging to removed resources return 404.
- No migration is required; comparison is derived from immutable revision history.

### Acceptance criteria

- Historical revision content remains independently inspectable.
- The UI distinguishes current guidance from superseded history.
- Comparison uses persisted revision bodies and does not mutate either revision.
- Added/removed body lines are understandable without an opaque score or generated interpretation.
- Revision-specific supporting sources remain visible.
- Removed resources do not expose historical content publicly.
- Tests cover history links, exact historical content, current/historical labels, comparison output, revision 1 behavior, missing revisions, and removed resources.

### Comparison decision

Story 11.3 intentionally starts with deterministic text comparison rather than AI-generated summaries. This keeps the historical record reproducible, inexpensive, and auditable. More sophisticated visual diff presentation can be added later without changing the revision model.

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
