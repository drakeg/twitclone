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

**Status:** Completed.

- Historical revisions have stable inspection pages with exact persisted content, editor attribution, timestamp, change note, and revision-specific source.
- Current and superseded revisions are explicitly distinguished.
- Deterministic line-level comparison shows added and removed body lines against the immediately preceding revision.
- Revision 1 has a clear no-previous-version state.
- Removed resources do not expose historical revisions publicly.
- Story 11.3 merged in PR #190, including a startup regression fix that keeps resource endpoints correctly namespaced.

## Story 11.4 — Resource discovery

**Status:** In implementation.

**Goal:** Make durable resources discoverable through Ripple's explicit topic system without converting knowledge discovery into paid placement or a hidden popularity ranking.

### Current implementation slice

- Existing `/topic/<slug>` discovery pages now include visible, non-removed resources explicitly associated with that normalized topic.
- Resource discovery uses the same explicit topic association created at publication; it does not infer topics from resource text or user attributes.
- Resources are ordered by `updated_at` descending and resource ID descending for deterministic ties.
- The ordering rule is disclosed on the topic page.
- Followers, subscriptions, paid plans, verification, and contributor reputation do not affect resource placement.
- Each result links directly to the durable resource and shows owner, current revision number, updated date, and a short current-content preview.
- Removed resources are excluded.
- Topics with no visible resources show a clear empty state.
- No schema migration is required because Story 11.1 already established normalized resource-topic associations.

### Acceptance criteria

- A resource appears on each topic page it was explicitly associated with.
- Removed resources do not appear.
- Resource ordering is deterministic and understandable.
- No follower count, paid entitlement, verification state, or reputation score buys placement.
- Low-data/empty topics remain useful and understandable.
- Topic contributor discovery remains separate from durable-resource ordering.
- Tests cover visible resources, ordering, links, exclusion of removed resources, ranking explanation, and empty state.

### Discovery decision

Story 11.4 uses recency of the resource's maintained state rather than social popularity. This is intentionally not a claim that the newest resource is the most authoritative; it is a transparent browsing order. Future resource quality/review signals require their own explicit, auditable design before they can affect discovery.

## Story 11.5 — Resource integrity and lifecycle

**Status:** Planned.

- Define moderation/removal behavior for resources and historical revisions.
- Keep source and attribution history understandable after corrections.
- Document ownership, contributor permissions, and future community integration boundaries.

## Definition of done

Sprint 11 is complete when Ripple supports durable, topic-associated resources that can be revised collaboratively with attribution and visible history, discovered without pay-to-win placement, and moderated without silently erasing provenance.
