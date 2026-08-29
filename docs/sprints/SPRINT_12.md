# Sprint 12 — Feed Choice and Relationship-First Discovery

**Status:** Completed.

## Goal

Give people meaningful, understandable control over what Ripple shows them without replacing one opaque engagement algorithm with another.

## Product principles

- Every feed mode has a plain-language explanation of what it includes and how it is ordered.
- A chronological/following feed remains available as a stable baseline.
- User choice is persistent and reversible rather than silently inferred.
- Paid plans, verification, follower counts, and engagement totals do not purchase organic placement.
- Ripple does not infer emotional state, political ideology, or sensitive interests to choose a feed.
- Discovery modes use data Ripple actually and transparently records.

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

**Status:** Completed.

- Authenticated users can explicitly choose **Quiet** from Home.
- Quiet includes the viewer's own direct activity plus direct posts, quotes, and polls from mutual connections only.
- A mutual connection means both accounts explicitly follow each other; one-way follows do not qualify.
- Reposts are excluded from Quiet even when performed by a mutual connection, reducing amplification noise by design.
- Results remain deterministic newest-first.
- Quiet is a temporary view and cannot be stored through `/feed-preference`.
- Anonymous requests for Quiet fall back to All Ripple.
- The UI explains the mutual-connection rule, repost exclusion, chronological order, and lack of popularity/engagement ranking.
- Pagination preserves `feed=quiet`.
- Story 12.4 merged in PR #198.

## Story 12.5 — Feed integrity and measurement

**Status:** Completed.

- `twitclone/timeline/integrity.py` declares the feed ordering contract, allowed inclusion inputs, forbidden ranking inputs, and measurement boundaries.
- Every Sprint 12 feed remains deterministic newest-first.
- Existing post-impression, profile-visit, and follower-snapshot analytics remain reporting signals only and are not feed-ranking inputs.
- Sprint 12 adds no feed-choice-history or topic-query-history analytics collection.
- Follower count, verification state, paid subscription/entitlement, engagement totals/velocity, and inferred sensitive traits are explicitly forbidden organic ranking inputs.
- `docs/FEED_INTEGRITY.md` documents anti-gaming, privacy, measurement, and regression expectations.
- Automated coverage verifies the policy constants and chronological ordering across All Ripple, Following, Quiet, and Topic modes.

### Product decision

Ripple intentionally separates **measurement** from **optimization**. Recording an impression for aggregate or creator analytics does not authorize using that impression count, or other engagement/reporting data, to reorder the feed. Any future non-chronological recommendation mode requires a separately specified product decision, user-facing explanation, privacy/integrity review, and regression coverage.

## Sprint outcome

Sprint 12 established four understandable feed experiences:

- **All Ripple** for a broad chronological view;
- **Following** for explicit one-way relationship filtering;
- **Topic** for author-declared subject discovery;
- **Quiet** for reciprocal relationships without repost amplification.

The sprint also established persistent/reversible defaults for the stable All Ripple/Following baseline and a documented integrity contract preventing hidden engagement, paid-placement, verification, follower-count, or sensitive-trait ranking.

## Definition of done

Completed. Ripple now offers understandable, reversible feed choices including a chronological/following baseline, explicit-topic discovery, relationship-first Quiet mode, persistent user preference where appropriate, and documented/tested feed-integrity boundaries without hidden engagement or sensitive-trait ranking.
