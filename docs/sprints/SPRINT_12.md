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

**Status:** In implementation.

### Current implementation slice

- Home adds an explicit **Explore a topic** control for authenticated users.
- Topic mode is a temporary browsing mode and cannot be persisted as the user's default feed.
- Topic input is normalized through Ripple's existing topic vocabulary and matched by normalized slug.
- Only posts with an author-selected `explicit` topic association qualify.
- Hashtag-only topic associations are intentionally excluded from topic discovery.
- Reposts qualify when the original post has the selected explicit topic association.
- Quotes are excluded because quote text has no independent topic association today; inheriting the quoted post's topic would imply intent that the quote author did not declare.
- Polls are excluded because polls do not yet support explicit topic associations.
- Results remain deterministic newest-first using the same timeline ordering rules as existing feeds.
- The UI explains the inclusion/exclusion rules and states that popularity/engagement ranking is not applied.
- Topic pagination preserves the normalized topic slug.
- Unknown topics produce a clear empty state rather than falling back to unrelated content.
- No migration is required.

### Acceptance criteria

- Explicitly associated posts appear for the selected topic.
- Hashtag-only matches do not appear.
- Reposts of explicitly associated posts appear.
- Quote posts and polls do not appear until they can carry their own explicit topic semantics.
- Topic mode cannot be saved through `/feed-preference`.
- Unknown topics return a clear empty topic feed.
- Pagination retains both `feed=topic` and the normalized topic slug.
- Feed explanation makes the deterministic rules visible to the user.
- Tests cover explicit-vs-hashtag filtering, repost inclusion, quote/poll exclusion, pagination, empty state, and persistence rejection.

### Product decision

Story 12.3 favors declared intent over broad matching. Ripple does not infer that a quote, poll, hashtag, profile attribute, engagement history, or other behavior represents a user's interest in a topic. Additional topic-follow persistence can be designed separately after the browsing semantics are validated.

## Story 12.4 — Relationship-first / quiet mode

**Status:** Planned.

Explore a deliberately lower-noise mode based on explicit relationships and understandable recency rules, not engagement velocity or outrage proxies.

## Story 12.5 — Feed integrity and measurement

**Status:** Planned.

Document ranking boundaries, anti-gaming expectations, measured usage signals, privacy constraints, and regression coverage before Sprint 12 closes.

## Definition of done

Sprint 12 is complete when Ripple offers understandable, reversible feed choices including a chronological/following baseline, transparent topic/relationship discovery where appropriate, persistent user preference, and documented integrity boundaries without hidden engagement or sensitive-trait ranking.
