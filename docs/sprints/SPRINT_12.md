# Sprint 12 — Feed Choice and Relationship-First Discovery

**Status:** In implementation.

## Goal

Give people meaningful, understandable control over what Ripple shows them without replacing one opaque engagement algorithm with another.

## Product principles

- Every feed mode must have a plain-language explanation of what it includes and how it is ordered.
- A chronological/following feed remains available as a stable baseline.
- User choice is persistent and reversible rather than silently inferred.
- Paid plans, verification, follower counts, and engagement totals do not purchase organic placement.
- Ripple does not infer emotional state, political ideology, or sensitive interests to choose a feed.
- New discovery modes must use data Ripple actually and transparently records.

## Story 12.1 — Explicit chronological feed choice

**Status:** Completed.

- Authenticated users can switch between **All Ripple** and **Following** from Home.
- All Ripple preserves the visible chronological timeline.
- Following includes content acted/published by followed accounts plus the viewer's own content.
- Posts, reposts, quotes, and polls follow the same relationship rule.
- Both modes are newest-first and explain their behavior directly in the UI.
- Pagination preserves the active mode; invalid values fall back safely.
- Story 12.1 merged in PR #193.

## Story 12.2 — Persistent and reversible feed preference

**Status:** Completed.

- A companion `UserFeedPreference` record stores an authenticated user's default feed mode.
- Migration `20260828_0026_feed_preference.py` constrains saved values to `all` or `following`.
- Users with no saved preference default to All Ripple.
- Query-string switching is temporary unless the user explicitly changes the default.
- Users can reverse the saved default between All Ripple and Following.
- Anonymous visitors cannot persist a feed preference.
- Story 12.2 merged in PR #194.

## Story 12.3 — Topic-oriented discovery mode

**Status:** Completed.

- Home provides an explicit **Explore a topic** control.
- Topic mode uses Ripple's normalized topic vocabulary and only author-selected `explicit` associations.
- Hashtag-only associations are excluded.
- Reposts qualify when the original post explicitly carries the selected topic.
- Quotes and polls are excluded until they can carry their own explicit topic semantics.
- Topic results remain deterministic newest-first and cannot be saved as the default feed.
- Unknown topics show an empty topic state rather than unrelated content.
- Story 12.3 implementation merged in PR #197. PR #196 was an empty administrative merge and is not treated as implementation evidence.

## Story 12.4 — Relationship-first / quiet mode

**Status:** In implementation.

### Current implementation slice

- Authenticated users can explicitly choose **Quiet** from Home.
- Quiet includes the viewer's own direct activity plus direct posts, quotes, and polls from **mutual connections** only.
- A mutual connection means both accounts explicitly follow each other; one-way follows do not qualify.
- Reposts are excluded from Quiet even when performed by a mutual connection, reducing amplification noise by design.
- Results remain deterministic newest-first.
- Quiet is a temporary view and cannot be stored through `/feed-preference` in this story.
- Anonymous requests for Quiet safely fall back to All Ripple.
- The UI explains the mutual-connection rule, repost exclusion, chronological order, and lack of popularity/engagement ranking.
- Pagination preserves `feed=quiet`.
- No migration is required.

### Acceptance criteria

- The viewer's own direct activity remains visible.
- Direct activity from mutual connections appears.
- One-way follows and unrelated accounts do not appear.
- Reposts do not appear, including reposts by mutual connections.
- Quotes and polls from mutual connections follow the same relationship rule as posts.
- Ordering remains newest-first and deterministic.
- Quiet cannot be persisted as the default feed.
- Anonymous Quiet requests fall back to All Ripple.
- Tests cover relationship boundaries, repost exclusion, UI explanation, pagination, persistence rejection, and anonymous fallback.

### Product decision

Quiet is intentionally narrower than Following. It is not a quality score or a hidden recommendation model; it is a transparent relationship filter based on reciprocal follows plus a deliberate removal of repost amplification. No follower count, engagement velocity, subscription, verification state, or inferred trait affects inclusion or ordering.

## Story 12.5 — Feed integrity and measurement

**Status:** Planned.

Document ranking boundaries, anti-gaming expectations, measured usage signals, privacy constraints, and regression coverage before Sprint 12 closes.

## Definition of done

Sprint 12 is complete when Ripple offers understandable, reversible feed choices including a chronological/following baseline, transparent topic/relationship discovery where appropriate, persistent user preference, and documented integrity boundaries without hidden engagement or sensitive-trait ranking.
