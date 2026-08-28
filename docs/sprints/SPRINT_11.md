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

**Status:** In implementation.

**Goal:** Establish a separate resource content type with attribution, initial revision history, sources, and explicit topic associations.

### Current implementation slice

- Adds a dedicated `/resources/` library separate from ordinary posts.
- Authenticated users can publish a resource with a title, body, optional supporting source URL, and up to five explicit topics.
- A new resource immediately creates revision 1 attributed to the author.
- The current resource view points to revision history rather than overwriting the original revision.
- Resource detail shows the current revision, source link, topics, author, and revision-history attribution.
- Removed resources are excluded from the library and return 404 from public detail.
- Topics reuse Sprint 10 normalization and duplicate handling.
- Migration `20260828_0024_resource_foundation.py` creates resources, revisions, and topic associations.

### Acceptance criteria

- Resources are stored separately from timeline posts.
- Creation requires authentication.
- A resource has a title and durable body content.
- Revision 1 is immutable history attributed to its author.
- Optional source URLs require HTTP or HTTPS.
- Explicit topics are normalized and duplicate-safe.
- Removed resources are not publicly listed or viewable.
- Tests cover creation, attribution, topic association, source validation, authorization, and empty-state behavior.

## Story 11.2 — Attributable collaborative revisions

**Status:** Planned.

- Add a controlled revision flow that appends a new revision rather than replacing history.
- Keep editor attribution and a concise change note.
- Define who may propose or publish revisions before adding broader collaboration.

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
