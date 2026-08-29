# Sprint 12 — Feed Choice and Relationship-First Discovery

**Status:** In implementation.

## Goal

Give people meaningful, understandable control over what Ripple shows them without replacing one opaque engagement algorithm with another.

## Product principles

- Every feed mode must have a plain-language explanation of what it includes and how it is ordered.
- A chronological/following feed remains available as a stable baseline.
- User choice should become persistent and reversible rather than silently inferred.
- Paid plans, verification, follower counts, and engagement totals do not purchase organic placement.
- Ripple does not infer emotional state, political ideology, or sensitive interests to choose a feed.
- New discovery modes must use data Ripple actually and transparently records.

## Story 12.1 — Explicit chronological feed choice

**Status:** In implementation.

### Current implementation slice

- Authenticated users can switch between **All Ripple** and **Following** from the Home timeline.
- All Ripple preserves the existing visible-content timeline ordered newest first.
- Following contains content acted/published by accounts the viewer follows plus the viewer's own content.
- Following applies consistently to normal posts, reposts, quote posts, and polls.
- Both modes retain the existing deterministic chronological ordering; no engagement/popularity score is introduced.
- The active mode and its ordering rule are explained directly above the feed.
- Pagination retains the selected feed query parameter.
- Invalid feed values safely fall back to All Ripple.
- Anonymous visitors retain the existing All Ripple behavior.
- No migration is required for this first slice; persistence is intentionally deferred to Story 12.2.

### Acceptance criteria

- Following excludes content acted/published only by unrelated accounts.
- The viewer's own content remains visible in Following.
- Reposts and quotes qualify based on the account performing the social action, not the original post author.
- Polls follow the same author relationship rule.
- Ordering remains newest-first and deterministic.
- UI explains the active mode rather than presenting it as an unexplained algorithm.
- Pagination does not silently switch modes.
- Tests cover followed/own/unrelated content, content types, explanation, pagination, and invalid mode fallback.

## Story 12.2 — Persistent and reversible feed preference

**Status:** Planned.

Persist an authenticated user's chosen default while keeping an obvious one-click way to switch modes and restore another default.

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
