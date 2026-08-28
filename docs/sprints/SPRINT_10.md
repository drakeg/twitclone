# Sprint 10 — Topic Reputation and Expertise

**Status:** In implementation.

## Goal

Help Ripple users find people who have demonstrated useful participation in specific topics without turning credibility into a global popularity score or a paid entitlement.

## Product hypothesis

Follower count and generic engagement are weak proxies for whether someone is consistently useful on a particular subject. Ripple already records constructive contribution signals and transparent fact-context review history. Topic-specific, explainable reputation can build on those foundations to help users discover useful contributors while avoiding a universal social score.

## Guardrails

- Reputation is topic-specific, never a single global human-worth or trust score.
- Paid status, subscriptions, identity badges, follower count, and raw impression volume do not increase topic reputation.
- Ripple does not infer political ideology, religion, health status, race, sexual orientation, or other sensitive traits to create topics, diversify reviewers, or score reputation.
- Users must be able to understand why a displayed reputation summary exists.
- Initial reputation is informational. It must not silently amplify or suppress feed reach.
- Self-awards and obvious reciprocal/gaming paths must not contribute.
- Reputation is derived from auditable activity rather than a mutable administrator-entered score.
- Existing constructive signals and community-context review history remain meaningful on their own; Sprint 10 does not relabel consensus as objective truth.

## Story 10.1 — Explicit topic foundation

**Status:** Completed.

- Normalized, duplicate-safe `Topic` records and `TweetTopic` associations are in place.
- Associations record whether the topic came from an explicit author choice or deterministic hashtag text.
- Authors can select up to five comma-separated explicit topics when composing a post.
- Hashtags remain deterministic discovery metadata and are not automatically expertise evidence.
- Existing posts need no backfill; removed posts expose no public topic associations.
- Timeline presentation preserves original/repost semantics without making Quote cards inherit another author's topics.
- Migration `20260828_0023_topic_foundation.py` and regression coverage merged in PR #182.

## Story 10.2 — Topic contribution evidence

**Status:** Completed.

- `topic_contribution_evidence()` derives evidence instead of storing a mutable reputation score.
- Only explicit topic associations qualify for constructive-signal evidence.
- Helpful, Thoughtful, and Useful context signals are counted separately.
- Eligible posts, recognized posts, and unique recognizers remain visible dimensions.
- Self-signals and removed posts are excluded.
- Toggling/deleting a constructive signal immediately changes derived evidence.
- Followers, impressions, subscriptions, identity badges, and paid status are excluded.
- Evidence service and regression coverage merged in PR #183.

## Story 10.3 — Explainable topic reputation summary

**Status:** Completed.

- Contributor/topic summaries are derived; no reputation value is persisted.
- Published multi-dimension levels are:
  - Building contribution history — eligible explicit-topic posts exist but recognition thresholds are not yet met.
  - Emerging contributor — at least 1 constructive signal across at least 1 recognized post from at least 1 unique recognizer.
  - Recognized contributor — at least 3 constructive signals across at least 2 recognized posts from at least 2 unique recognizers.
  - Established contributor — at least 5 constructive signals across at least 3 recognized posts from at least 3 unique recognizers.
- Profiles show the level plus eligible posts, recognized posts, unique recognizers, total signals, and per-signal counts.
- Profiles state that topic reputation does not affect feed ranking or moderation authority.
- Hashtag-only topics do not appear in reputation summaries.
- Profile summaries and threshold regression coverage merged in PR #184.

## Story 10.4 — Discovery integration

**Status:** Completed.

- `/topic/<slug>` surfaces contributors with eligible explicit-topic contribution history.
- Hashtag-only posts do not qualify an author for expertise discovery.
- Contributor cards show the same transparent evidence dimensions used on profiles.
- Profile topic names link into topic discovery.
- Ordering is disclosed and deterministic: contribution level, unique recognizers, recognized posts, constructive signals, then username for ties.
- Followers, impressions, subscriptions, paid plans, and verification do not affect qualification or placement.
- Existing low-data topics degrade gracefully and unknown topic slugs return 404.
- Discovery implementation and regression coverage merged in PR #186.

## Story 10.5 — Integrity and correction controls

**Status:** In implementation.

**Goal:** Make the reputation system correctable and resistant to obvious gaming without introducing manually editable scores.

### Current implementation slice

- Post authors can correct the explicit topics on their own non-removed posts from post detail.
- Topic correction replaces only the author-selected topic associations. Hashtag associations are rebuilt deterministically from unchanged post text.
- If an explicit topic is removed but still appears as a hashtag, it remains discovery metadata but immediately stops qualifying as expertise evidence.
- Moving an explicit association from one topic to another immediately moves the post's constructive evidence because summaries are recomputed from source records.
- Non-authors receive `403` when attempting to change another author's explicit topics; removed posts cannot be corrected through the route.
- Toggling a constructive signal off immediately removes it from topic evidence.
- Multiple distinct signal types from one person remain separate signal counts but count as only one unique recognizer, reducing a simple multi-click inflation path.
- Removed/moderated source posts immediately stop contributing to profile summaries and topic discovery.
- No administrator or author can directly edit a reputation level or score because no such stored score exists.
- No schema migration is required for this slice.

### Acceptance criteria

- Deleted/removed/ineligible source activity stops contributing according to documented rules.
- Duplicate/self/obvious multi-signal gaming paths are covered by constraints or regression tests.
- Corrections to explicit topic association are reflected in derived summaries without manual score editing.
- Toggled-off constructive signals stop contributing immediately.
- Hashtag-only associations remain discovery metadata rather than expertise evidence after a correction.
- Any future use of reputation for elevated permissions requires a separate sprint/decision and is not implied by Sprint 10.

## Integrity behavior reference

- **Constructive signal toggled off:** the source row is deleted; the next evidence calculation no longer counts it.
- **Post removed/moderated:** the post no longer qualifies as evidence or contributor-discovery input even if historical contribution rows remain for audit/history purposes.
- **Explicit topic corrected:** evidence follows the current explicit association; no reputation record is manually moved or edited.
- **Explicit topic cleared but hashtag remains:** the topic remains discoverable from post text but contributes zero expertise evidence from that post.
- **Multiple signal categories from one recognizer:** categories remain visible separately while unique-recognizer count remains one.
- **Paid/follower changes:** no reputation evidence or discovery placement changes because those fields are outside the derivation rules.

## Definition of done

Sprint 10 is complete when Ripple can associate eligible activity with explicit topics, derive explainable topic-specific contribution history, display it transparently, use it for non-pay-to-win discovery, and correct source associations without hidden ranking, manual reputation editing, or sensitive-trait inference.

## Explicitly deferred

- Reputation-weighted moderation or community-context votes
- Reputation-based feed amplification/suppression
- Paid reputation boosts
- Cross-topic/global trust scores
- AI-inferred expertise or sensitive-interest profiles
- Elevated permissions based on topic reputation
- Communities/topic spaces, which are planned for Sprint 13
