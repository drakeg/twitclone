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
- Topic mode is temporary and cannot become the saved default feed.
- Only author-selected explicit topic associations qualify.
- Hashtag-only associations do not qualify.
- Reposts qualify when the original post has the selected explicit topic.
- Quotes and polls are excluded until they can carry their own explicit topic semantics.
- Results remain deterministic newest-first with no popularity or engagement ranking.
- Unknown topics show a clear empty state rather than unrelated content.
- Story 12.3 merged in PR #197. PR #196 was an empty administrative merge and is not considered the implementation evidence.

## Story 12.4 — Relationship-first / quiet mode

**Status:** In implementation.

### Current implementation slice

- Authenticated users can select a temporary **Quiet** feed from Home.
- Quiet uses only explicit follow relationships plus the viewer's own account.
- Quiet includes original posts and polls from those accounts.
- Reposts and quote posts are intentionally excluded to remove amplification layers while retaining direct authored content.
- Quiet remains newest-first and deterministic.
- No engagement velocity, follower count, paid entitlement, verification status, topic inference, or sentiment signal affects inclusion or order.
- Quiet cannot be persisted as the default feed in this story; saved defaults remain All Ripple or Following.
- Anonymous requests for Quiet fall back to All Ripple rather than creating a pseudo-personalized anonymous feed.
- Pagination preserves `feed=quiet`.
- No migration is required.

### Acceptance criteria

- Direct posts from followed accounts and the viewer appear in Quiet.
- Direct posts from unrelated accounts do not appear.
- Polls authored by followed accounts remain visible as direct authored content.
- Reposts and quote posts are excluded even when the amplification action came from a followed account.
- Ordering remains deterministic newest-first.
- The UI explains exactly what Quiet includes and excludes.
- Quiet cannot be persisted through `/feed-preference`.
- Anonymous Quiet requests safely fall back to All Ripple.
- Tests cover relationship filtering, amplification suppression, UI explanation, pagination, persistence rejection, and anonymous fallback.

### Product decision

Quiet is not a hidden ranking algorithm. It is a transparent content-type reduction layered on the user's explicit relationship graph: direct authored posts and polls from people they chose to follow, plus their own. It deliberately suppresses repost and quote amplification rather than trying to predict which content is calming, healthy, agreeable, or emotionally appropriate.

## Story 12.5 — Feed integrity and measurement

**Status:** Planned.

Document ranking boundaries, anti-gaming expectations, measured usage signals, privacy constraints, and regression coverage before Sprint 12 closes.

## Definition of done

Sprint 12 is complete when Ripple offers understandable, reversible feed choices including a chronological/following baseline, transparent topic/relationship discovery where appropriate, persistent user preference, and documented integrity boundaries without hidden engagement or sensitive-trait ranking.
