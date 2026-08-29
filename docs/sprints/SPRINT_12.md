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

**Status:** In implementation.

### Current implementation slice

- A companion `UserFeedPreference` record stores an authenticated user's default feed mode without modifying the mature `User` table model.
- Migration `20260828_0026_feed_preference.py` creates one preference row per user with a database constraint limiting values to `all` or `following`.
- Users with no saved preference default to All Ripple, preserving existing behavior.
- Visiting `/?feed=...` temporarily switches the current view without mutating the saved default.
- The Home UI states the saved default separately from the currently viewed feed.
- When the current feed differs from the saved default, an explicit **Make ... my default** control is shown.
- `POST /feed-preference` creates or replaces the preference only after an authenticated, explicit action.
- Invalid stored/write values do not produce a third implicit feed mode.
- The preference is reversible by making either All Ripple or Following the default.
- Anonymous visitors cannot persist a feed preference.

### Acceptance criteria

- A saved Following preference is applied on a plain `/` visit with no query parameter.
- A temporary query-string switch does not alter the saved preference.
- A user can change the saved default in either direction.
- Invalid preference submissions return 400 and do not mutate data.
- Unauthenticated preference writes are rejected by authentication.
- The UI distinguishes **current view** from **saved default** so switching is understandable and reversible.
- No follower count, engagement metric, paid entitlement, or inferred trait influences preference selection.
- Tests cover default application, temporary switching, replacement, invalid input, and authentication.

### Data-model decision

Story 12.2 uses a companion preference table rather than adding another column to the mature `User` table. This keeps the feed-choice feature isolated, makes future feed modes easier to evolve, and avoids unrelated model churn.

## Story 12.3 — Topic-oriented discovery mode

**Status:** Planned.

Use explicit topic follows/interests and existing normalized topic associations to provide a transparent topic-oriented browsing mode without inferred sensitive interests.

## Story 12.4 — Relationship-first / quiet mode

**Status:** Planned.

Explore a deliberately lower-noise mode based on explicit relationships and understandable recency rules, not engagement velocity or outrage proxies.

## Story 12.5 — Feed integrity and measurement

**Status:** Planned.

Document ranking boundaries, anti-gaming expectations, measured usage signals, privacy constraints, and regression coverage before Sprint 12 closes.

## Definition of done

Sprint 12 is complete when Ripple offers understandable, reversible feed choices including a chronological/following baseline, transparent topic/relationship discovery where appropriate, persistent user preference, and documented integrity boundaries without hidden engagement or sensitive-trait ranking.
