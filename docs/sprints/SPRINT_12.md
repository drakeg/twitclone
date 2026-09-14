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

- A companion `UserFeedPreference` record stores an authenticated user's default feed mode without modifying the mature `User` table model.
- Migration `20260828_0026_feed_preference.py` creates one preference row per user with a database constraint limiting values to `all` or `following`.
- Users with no saved preference default to All Ripple.
- Visiting `/?feed=...` temporarily switches the current view without mutating the saved default.
- The Home UI distinguishes the saved default from the currently viewed feed.
- Users can explicitly make All Ripple or Following their default and reverse that choice later.
- Anonymous visitors cannot persist a feed preference.
- Story 12.2 merged in PR #194.

## Story 12.3 — Topic-oriented discovery mode

**Status:** Completed.

- Home adds an explicit **Explore a topic** control for authenticated users.
- Topic mode is temporary and cannot be persisted as the user's default feed.
- Only author-selected `explicit` topic associations qualify; hashtag-only associations are excluded.
- Reposts qualify when the original post has the selected explicit topic.
- Quotes and polls are excluded until they can carry their own explicit topic semantics.
- Results remain deterministic newest-first with no popularity/engagement ranking.
- Unknown topics produce a clear empty state rather than unrelated fallback content.
- Story 12.3 merged in PR #197.

## Story 12.4 — Relationship-first / quiet mode

**Status:** In implementation.

### Current implementation slice

- Authenticated users can temporarily switch to **Quiet** from Home.
- Quiet includes the viewer's own original posts and polls.
- Quiet includes original posts and polls from accounts where the follow relationship is mutual.
- One-way follows do not qualify.
- Reposts and quotes are intentionally excluded to reduce amplification/noise rather than reproducing Following under another name.
- Ordering remains deterministic newest-first.
- Quiet does not use likes, repost counts, replies, follower counts, paid status, verification, engagement velocity, sentiment, or inferred interests.
- Quiet is temporary and cannot be saved through the existing feed-preference endpoint.
- Anonymous requests for Quiet fall back to All Ripple.
- No migration is required.

### Acceptance criteria

- The viewer's own original posts and polls appear.
- Original posts and polls from mutual follows appear.
- Content from one-way follows and unrelated accounts does not appear.
- Reposts and quotes do not appear, including when created by a mutual follow.
- Results remain newest-first and deterministic.
- The UI explains mutual-follow scope and the repost/quote exclusion.
- Quiet cannot be persisted as the default feed.
- Anonymous Quiet requests do not expose a relationship-only view.
- Tests cover relationship filtering, content-type filtering, UI explanation, temporary-only behavior, and anonymous fallback.

### Product decision

Quiet treats mutual following as the narrowest explicit relationship Ripple already records. It does not infer "close friends," score relationship strength, or estimate emotional relevance. Excluding reposts and quotes keeps the mode focused on what those relationships directly publish rather than what they amplify.

## Story 12.5 — Feed integrity and measurement

**Status:** Planned.

Document ranking boundaries, anti-gaming expectations, measured usage signals, privacy constraints, and regression coverage before Sprint 12 closes.

## Definition of done

Sprint 12 is complete when Ripple offers understandable, reversible feed choices including a chronological/following baseline, transparent topic/relationship discovery where appropriate, persistent user preference, and documented integrity boundaries without hidden engagement or sensitive-trait ranking.
