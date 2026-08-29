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

**Status:** Completed.

- Topic pages surface visible resources through explicit normalized resource-topic associations.
- Resources are ordered transparently by most recently maintained, with deterministic ID ties.
- Followers, subscriptions, paid plans, verification, and contributor reputation do not buy placement.
- Removed resources are excluded and empty topics have a clear durable-resource state.
- Story 11.4 merged in PR #191.

## Story 11.5 — Resource integrity and lifecycle

**Status:** In implementation.

**Goal:** Remove unsafe, obsolete, or unwanted resources from public Ripple without silently destroying the provenance that makes durable collaborative knowledge auditable.

### Current implementation slice

- Resource owners and administrators can remove a visible resource from public Ripple.
- Removal is a lifecycle state change, not a destructive delete.
- Every removal requires a retained reason and records `removed_at` plus the account that performed the action.
- Removed resources disappear from the resource library, topic discovery, current detail, and historical revision routes.
- Stored revision rows, editor attribution, change notes, and sources remain intact in the database for audit/provenance purposes.
- Removed resources cannot receive new revisions.
- Unrelated users cannot remove another user's resource.
- Administrator removals are attributed to the administrator rather than the resource owner.
- Migration `20260828_0025_resource_lifecycle.py` adds lifecycle audit metadata without altering immutable revision records.

### Acceptance criteria

- Public removal never hard-deletes resource revision history.
- The remover, removal time, and reason are retained.
- Owner/admin authority is explicit and unrelated users receive 403.
- Removed resources return 404 from current and historical public routes and remain absent from discovery.
- Removed resources cannot be revised after removal.
- Existing revision provenance remains queryable internally after removal.
- Tests cover owner removal, administrator attribution, unauthorized removal, required reason, provenance preservation, public hiding, and post-removal revision blocking.

### Lifecycle decision

Sprint 11 deliberately separates public visibility from provenance retention. Removal means Ripple stops serving or discovering the resource; it does not rewrite history. A future legal/privacy deletion workflow may require stronger erasure semantics and must be designed separately rather than overloading moderation removal.

## Sprint completion gate

After Story 11.5 merges and its validation passes, Sprint 11 can be marked **Completed**. The resulting resource system provides durable topic-associated knowledge, append-only attributable revisions, inspectable history, transparent topic discovery, and non-destructive moderation lifecycle controls.

## Definition of done

Sprint 11 is complete when Ripple supports durable, topic-associated resources that can be revised collaboratively with attribution and visible history, discovered without pay-to-win placement, and moderated without silently erasing provenance.
