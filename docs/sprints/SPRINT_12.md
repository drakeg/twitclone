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

- Home provides an explicit topic browsing mode using Ripple's normalized topic vocabulary.
- Only author-selected explicit topic associations qualify; hashtag-only associations do not.
- Reposts qualify from the original post's explicit topic, while quotes and polls are excluded until they have their own topic semantics.
- Topic mode is temporary, newest-first, and cannot be persisted as a default feed.
- Unknown topics produce a clear empty state and pagination preserves the topic slug.
- Story 12.3 merged in PR #197. PR #196 was an empty administrative merge and did not implement the story.

## Story 12.4 — Relationship-first / quiet mode

**Status:** In implementation.

### Current implementation slice

- Quiet mode is available only to authenticated users because it depends on explicit follow relationships.
- It includes original posts and polls from accounts the viewer explicitly follows plus the viewer's own original posts and polls.
- Reposts and quotes are omitted deliberately to reduce amplification, repetition, and second-hand conversation traffic.
- Content remains deterministic newest-first; Quiet does not score relationship strength or reorder by engagement.
- Follower counts, verification, paid status, contribution reputation, impressions, clicks, and engagement totals have no influence.
- Ripple does not infer close friends, emotional state, political alignment, or sensitive interests to decide who belongs in Quiet.
- Quiet is a temporary view in this story and is not added to persisted defaults without a separate explicit product decision.
- Anonymous requests for Quiet fall back to All Ripple.
- No migration is required.

### Acceptance criteria

- Followed accounts' original posts and polls appear in Quiet.
- The viewer's own original posts and polls appear in Quiet.
- Unfollowed accounts' content does not appear.
- Reposts and quotes do not appear even when the actor is followed.
- Ordering remains deterministic newest-first.
- Quiet cannot be submitted to `/feed-preference` as a persisted default.
- Anonymous visitors do not receive a relationship-derived feed.
- Tests cover relationship filtering, own content, polls, amplification exclusions, authentication, and persistence rejection.

### Product decision

Quiet is intentionally simpler than an algorithmic "close friends" feed. The relationship signal is binary and user-declared: followed or not followed. Omitting reposts and quotes reduces amplification without Ripple deciding which people, subjects, or reactions deserve more attention.

## Story 12.5 — Feed integrity and measurement

**Status:** Planned.

Document ranking boundaries, anti-gaming expectations, measured usage signals, privacy constraints, and regression coverage before Sprint 12 closes.

## Definition of done

Sprint 12 is complete when Ripple offers understandable, reversible feed choices including a chronological/following baseline, transparent topic/relationship discovery where appropriate, persistent user preference, and documented integrity boundaries without hidden engagement or sensitive-trait ranking.
