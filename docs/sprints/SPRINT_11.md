# Sprint 11 — Collaborative Knowledge and Resource Posts

**Status:** Completed.

## Goal

Give Ripple a durable knowledge layer for guides, checklists, references, and community-maintained resources that should outlive an ordinary timeline post.

## Product hypothesis

Some useful contributions should be improved over time instead of repeatedly reposted into a feed. A resource preserves attribution, revisions, supporting sources, and topic context so readers can understand both the current guidance and how it evolved.

## Guardrails

- Resource posts are distinct from ordinary timeline posts.
- Revision history is append-only; edits do not silently erase prior contributions.
- Each revision records the contributing account and time.
- Supporting sources remain visible when supplied.
- Topics reuse Ripple's explicit normalized topic vocabulary.
- Contributor or reviewer permissions are not purchased through a subscription or popularity metric.
- Sprint 11 does not create communities or topic-space membership; that remains Sprint 13 work.
- No feed ranking changes, AWS activation, or paid service were introduced by this sprint.

## Delivered stories

### Story 11.1 — Durable resource foundation — Completed

A dedicated `/resources/` library stores durable resources separately from ordinary posts. Publication creates immutable revision 1 with author attribution, optional source, and normalized explicit topics. Migration `20260828_0024_resource_foundation.py` merged in PR #188.

### Story 11.2 — Attributable collaborative revisions — Completed

Owners and administrators can publish append-only revisions with editor attribution and required change notes. Unrelated users cannot directly edit a resource, and payment/popularity does not grant edit authority. Merged in PR #189.

### Story 11.3 — Revision review and comparison — Completed

Historical revisions have stable inspection pages with exact content, attribution, revision-specific sources, and deterministic line-level comparison. Removed resources do not expose revision history publicly. Merged in PR #190.

### Story 11.4 — Resource discovery — Completed

Topic pages surface visible resources through explicit normalized topic associations using transparent maintained-recency ordering. Paid plans, follower counts, verification, and contributor reputation do not buy placement. Merged in PR #191.

### Story 11.5 — Resource integrity and lifecycle — Completed

Owners and administrators can remove resources from public Ripple without hard-deleting provenance. Removal requires a reason and records remover/time; all stored revisions remain intact internally, while removed resources disappear from public library, discovery, detail, and revision routes and cannot receive new revisions. Migration `20260828_0025_resource_lifecycle.py` merged in PR #192.

## Sprint outcome

Sprint 11 delivered durable topic-associated knowledge, append-only attributable revisions, inspectable history, transparent topic discovery, and non-destructive moderation lifecycle controls. Public visibility and provenance retention are intentionally separate. A future legal/privacy erasure workflow requires its own explicit design rather than silently rewriting collaborative history.

## Definition of done

Completed. Ripple supports durable, topic-associated resources that can be revised with attribution and visible history, discovered without pay-to-win placement, and moderated without silently erasing provenance.
